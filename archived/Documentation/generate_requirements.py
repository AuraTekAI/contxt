import subprocess

# Function to get the list of installed packages
def get_installed_packages():
    result = subprocess.run(['pip', 'freeze'], stdout=subprocess.PIPE, text=True)
    return result.stdout.strip()

# Function to save the list of packages to a requirements file
def save_requirements_file(packages, filename='requirements.txt'):
    with open(filename, 'w') as file:
        file.write(packages)

def main():
    packages = get_installed_packages()
    save_requirements_file(packages)
    print(f"Requirements file generated with {len(packages.splitlines())} packages.")

if __name__ == "__main__":
    main()
