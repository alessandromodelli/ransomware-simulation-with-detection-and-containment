import os
import random
import argparse


#Types of extensions
extensions = [
    "txt", "csv", "pdf", "png", "jpg"
]

def random_string_gen(n=50):
    dictionary = [
    "casa",
    "strada",
    "montagna",
    "fiume",
    "albero",
    "vento",
    "mare",
    "pioggia",
    "sole",
    "notte",
    "gatto",
    "cane",
    "uomo",
    "donna",
    "bambino",
    "scuola",
    "libro", 
    "penna",
    "tavolo",
    "sedia",
]
    return ' '.join(random.choices(dictionary, k=n))


def file_gen(n = 20, target="target"):
    #Define output folder where the files will be created
    output_folder = target
    os.makedirs(output_folder, exist_ok=True)

    for i in range(n):
        ext = random.choice(extensions)
        file_name = f"file_{i}.{ext}"
        file_path = os.path.join(output_folder, file_name)

        #If it is a binary file create dummy bites
        if ext in ["png", "jpg", "pdf"]:
            with open(file_path, "wb") as f:
                f.write(os.urandom(random.randint(256, 10000000))) #write a random number of bytes between 256 and 10000000(10MB) random bytes
        
        else:
            with open(file_path, "w") as f:
                f.write(f"Fake content\n")
                f.write(random_string_gen(200))
        print(f"Created {file_name}")
    print(f"Created {n} fake files inside the directory /{output_folder}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate fake files")
    parser.add_argument("--target", type=str, default="target", help="Output folder")
    parser.add_argument("--amount", type=int, default=20, help="Number of files to be generated")
    args = parser.parse_args()
    file_gen(args.amount, args.target)
    