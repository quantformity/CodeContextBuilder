import click
import pathlib
from .core import Scanner

@click.group()
def main():
    """Code Context Builder - Create an agent-friendly index of your codebase."""
    pass

@main.command()
@click.argument('path', default='.')
def scan(path):
    """Scan the codebase and generate context files."""
    scanner = Scanner()
    scanner.scan(path)
    click.echo("Scan complete!")

@main.command()
def init():
    """Interactively configure LLM settings and create .ccbenv."""
    click.echo("🚀 Code Context Builder - Configuration")
    
    provider = click.prompt(
        "Select LLM Provider",
        type=click.Choice(['gemini', 'claude', 'openai', 'ollama', 'lmstudio', 'llamacpp'], case_sensitive=False),
        default='ollama'
    )
    
    model = click.prompt("Enter Model Name (e.g. gpt-4o, llama3, gemini-1.5-flash)", default='llama3')
    
    api_key = ""
    if provider in ['gemini', 'claude', 'openai']:
        api_key = click.prompt("Enter API Key", hide_input=True)
    
    base_url = ""
    if provider in ['ollama', 'lmstudio', 'llamacpp']:
        default_url = "http://localhost:11434" if provider == 'ollama' else "http://localhost:1234/v1"
        base_url = click.prompt("Enter Base URL", default=default_url)

    output_file = click.prompt("Output filename for context", default=".context.md")

    env_content = f"""# CCB Configuration
LLM_PROVIDER={provider}
LLM_MODEL={model}
LLM_API_KEY={api_key}
LLM_BASE_URL={base_url}
OUTPUT_FILE_NAME={output_file}
"""
    
    with open(".ccbenv", "w") as f:
        f.write(env_content)
    
    click.echo(click.style("\n✅ .ccbenv created successfully!", fg="green"))
    click.echo("You can now run 'ccb scan' to index your codebase.")

if __name__ == "__main__":
    main()
