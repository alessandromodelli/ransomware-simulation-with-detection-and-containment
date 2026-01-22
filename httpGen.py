import time
import random
import requests
import argparse

from datetime import datetime

def http_request_generator(url, interval, duration):
    end_time = time.time() + duration #Set ora di fine
    print(f"Starting generation to {url} for {duration}s with interval {interval}s\n")

    while time.time() < end_time:
        try:
			#Invio richieste a url
            start = time.time()
            response = requests.get(url, timeout=5)
            latency = (time.time() - start)*1000 #in ms
            print(f"[{datetime.now().strftime('%H:%M:%S')}] GET {url} -> {response.status_code} | {latency:.2f} ms")
        except requests.RequestException as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Errore: {e}\n")

        #Intervallo random tra una richiesta e l'altra tra 80% e 120% del parametro indicato(4 di default)
        sleep_time = random.uniform(interval * 0.8, interval * 1.2)
        time.sleep(sleep_time)
    print(f"Generation completed")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTTP traffic")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--interval", type=float, default=4.0, help="Interval between requests")
    parser.add_argument("--duration", type=int, default=60, help="Duration of the generation")
    args = parser.parse_args()

    http_request_generator(args.url, args.interval, args.duration)
