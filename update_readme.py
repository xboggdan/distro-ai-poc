import os
import subprocess

# CONFIGURATION
README_PATH = "README.md"
START_MARKER = ""
END_MARKER = ""

def get_app_description():
    """
    Run your app to get its precise help text/output.
    Change the command inside subprocess.check_output to match your app.
    Examples: 
      - ["python", "app.py", "--help"] 
      - ["npm", "start", "--", "--help"]
    """
    try:
        # REPLACE THIS with your actual command to get the app status/help
        # For now, I am simulating a precise description output
        output = subprocess.check_output(["python", "main.py", "--help"], text=True)
        return f"\n```text\n{output}\n```\n"
    except Exception as e:
        return f"\nError generating docs: {e}\n"

def update_readme():
    with open(README_PATH, "r") as file:
        content = file.read()

    description = get_app_description()
    
    # Logic to replace text between markers
    start_index = content.find(START_MARKER)
    end_index = content.find(END_MARKER)

    if start_index != -1 and end_index != -1:
        new_content = (
            content[:start_index + len(START_MARKER)] +
            description +
            content[end_index:]
        )
        
        if new_content != content:
            with open(README_PATH, "w") as file:
                file.write(new_content)
            print("✅ README.md updated with precise app details.")
            return True
        else:
            print("Example: README is already up to date.")
            return False
    else:
        print("⚠️ Markers not found in README.md")
        return False

if __name__ == "__main__":
    update_readme()
