from google.cloud import bigquery
from google.cloud import compute_v1
import json
from datetime import datetime


def firewall_automation(request):
    """
    Rileva potenziali data exfiltration e blocca automaticamente il traffico
    creando/aggiornando regole firewall
    """
    try:
        # Inizializza i client
        bq_client = bigquery.Client()
        firewall_client = compute_v1.FirewallsClient()
        instance_client = compute_v1.InstancesClient()
        
        project_id = "gruppo1-russo"
        
        # Query di rilevamento data exfiltration
        query = """
        -- PARAMETRI
        DECLARE WINDOW_MINUTES INT64 DEFAULT 1;
        DECLARE MIN_EVENTS INT64 DEFAULT 5;
        DECLARE MIN_BYTES_PER_EVENT INT64 DEFAULT 25 * 1024;  -- 25 KB

        WITH rs_logs_flat AS(
        SELECT
        timestamp,
        PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', jsonPayload.start_time) AS start_time,
        PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', jsonPayload.end_time) AS end_time,
        jsonPayload.connection.src_ip AS src_ip,
        jsonPayload.connection.dest_ip AS dest_ip,
        jsonPayload.connection.src_port AS src_port,
        jsonPayload.connection.dest_port AS dest_port,
        CAST(jsonPayload.bytes_sent AS INT64) AS bytes_sent,
        CAST(jsonPayload.packets_sent AS INT64) AS packets_sent,
        jsonPayload.reporter AS reporter,
        jsonPayload.src_instance.vm_name AS src_vm,
        jsonPayload.dest_instance.vm_name AS dest_vm,
        jsonPayload.connection.protocol AS protocol
        FROM `gruppo1-russo.rs_logs.networkmanagement_googleapis_com_vpc_flows_*`
        WHERE
            _TABLE_SUFFIX = FORMAT_DATE('%Y%m%d', CURRENT_DATE())
            AND PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%E*S%Ez', jsonPayload.start_time) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 4 MINUTE)
            AND NOT (STARTS_WITH(jsonPayload.connection.src_ip , '142.')
            OR STARTS_WITH(jsonPayload.connection.src_ip , '216.')
            OR STARTS_WITH(jsonPayload.connection.src_ip , '192.')
            OR STARTS_WITH(jsonPayload.connection.dest_ip, '142.')
            OR STARTS_WITH(jsonPayload.connection.dest_ip, '216.')
            OR STARTS_WITH(jsonPayload.connection.dest_ip, '192.'))
        ),

        filtered_logs AS (
        -- Step 1: remove noise from low bytes_sent
        SELECT
            src_vm,
            dest_vm,
            dest_port,
            start_time,
            bytes_sent
        FROM rs_logs_flat
        WHERE 
            bytes_sent IS NOT NULL
            AND bytes_sent >= MIN_BYTES_PER_EVENT
        ),

        windowed_logs AS (
        -- Step 2: assign logs to fixed 1-minute windows
        SELECT
            src_vm,
            dest_vm,
            dest_port,
            TIMESTAMP_SECONDS(
            DIV(UNIX_SECONDS(start_time), WINDOW_MINUTES * 60)
            * WINDOW_MINUTES * 60
            ) AS time_window,
            bytes_sent
        FROM filtered_logs
        )

        -- Step 3: detection rule with count of events and bytes_sent
        SELECT
        src_vm,
        dest_vm,
        dest_port,
        time_window,
        COUNT(*) AS event_count
        FROM windowed_logs
        GROUP BY src_vm, dest_vm, dest_port, time_window
        HAVING
        COUNT(*) >= MIN_EVENTS
        ORDER BY time_window DESC;
        """
        
        # Esegui la query
        query_job = bq_client.query(query)
        results = query_job.result()
        
        # Analizza i risultati e crea regole firewall
        suspicious_vms = []
        actions_taken = []

        vms_shutdown = [] 
        instances_actions_taken = []

        for row in results:
            vm_info = {
                "src_vm": row.src_vm,
                "dest_vm": row.dest_vm,
                "dest_port": row.dest_port,
                "time_window": row.time_window.isoformat(),
                "event_count": row.event_count
            }
            suspicious_vms.append(vm_info)
            
            # Crea una regola firewall per bloccare il traffico dalla VM sospetta
            firewall_rule_name = f"block-exfiltration-{row.src_vm.replace('_', '-')}"
            
            try:
                # Verifica se la regola esiste già
                try:
                    existing_rule = firewall_client.get(
                        project=project_id,
                        firewall=firewall_rule_name
                    )
                    action = f"Regola '{firewall_rule_name}' già esistente, non modificata"
                except Exception:
                    # La regola non esiste, creala
                    firewall_rule = compute_v1.Firewall()
                    firewall_rule.name = firewall_rule_name
                    firewall_rule.network = (
                        f"projects/{project_id}/global/networks/rs-lab-vpc"
                    )
                    firewall_rule.direction = "EGRESS"
                    firewall_rule.priority = 1000
                    firewall_rule.disabled = False
                    
                    # Blocca traffico in uscita dalla VM verso la destinazione
                    firewall_rule.denied = [
                        compute_v1.Denied(
                            I_p_protocol="tcp",
                            ports=[str(int(row.dest_port))] if row.dest_port else []
                        )
                    ]
                    
                    # Target: VM sorgente (quella che sta esfiltrando dati)
                    firewall_rule.target_tags = [row.src_vm]
                    
                    # Destinazione: qualsiasi IP o specifico se disponibile
                    firewall_rule.destination_ranges = ["0.0.0.0/0"]
                    
                    firewall_rule.description = (
                        f"AUTO-GENERATED: Blocco data exfiltration rilevata - {row.event_count} eventi rilevati"
                    )
                    
                    # Crea la regola
                    firewall_client.insert(
                        project=project_id,
                        firewall_resource=firewall_rule
                    )
                
                    action = f"✓ Creata regola '{firewall_rule_name}' per bloccare {row.src_vm}"
                
                actions_taken.append(action)
                
            except Exception as fw_error:
                actions_taken.append(f"✗ Errore creazione regola per {row.src_vm}: {str(fw_error)}")

            try: 
                #Spegni la vm sospetta
                instance_client.stop(
                    project=project_id,
                    zone="europe-west8-b",
                    instance=row.src_vm
                )

                vms_shutdown.append(row.src_vm)
                instances_actions_taken.append(f"✓ VM '{row.src_vm}' spenta con successo")

                print(f"ALERT: VM {row.src_vm} spenta per esfiltrazione dati - {row.event_count} eventi rilevati")
                
            except Exception as vm_error:
                instances_actions_taken.append(f"✗ Errore spegnimento VM {row.src_vm}: {str(vm_error)}")
        
        # Prepara la risposta
        response = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat(),
            "suspicious_activities_detected": len(suspicious_vms),
            "suspicious_vms": suspicious_vms,
            "firewall_actions": actions_taken,
            "instances_actions": instances_actions_taken,
            "message": f"Rilevate {len(suspicious_vms)} attività sospette. {len(actions_taken)+len(instances_actions_taken)} azioni eseguite."
        }
        
        return (json.dumps(response, indent=2), 200, {'Content-Type': 'application/json'})
        
    except Exception as e:
        error_response = {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "message": str(e),
            "type": type(e).__name__
        }
        return (json.dumps(error_response, indent=2), 500, {'Content-Type': 'application/json'})