# Email Campaign Generator

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Local Setup](#local-setup)
4. [Colab Setup](#colab-setup)
5. [Usage](#usage)
6. [Troubleshooting](#troubleshooting)
7. [Additional Notes](#additional-notes)

## Overview

This Email Campaign Generator is a powerful tool that leverages AI to create personalized email campaigns. It uses a combination of local Language Models (LLMs) via Ollama and cloud-based services to generate tailored email content for various products and campaign types.

The system is designed to run in two environments:
1. Local machine(using app.py)
2. Google Colab (using app_colab.py)

Both setups rely on Ollama for running local LLMs, which is crucial for the functioning of this application.

## Prerequisites

- Python 3.7+
- pip (Python package manager)
- Git
- Ollama (for running local LLMs)
- Streamlit (for the web interface)
- A Tavily API key
- (For Colab) A Google account with access to Google Colab

## Local Setup

1. Clone the repository

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Install Ollama:
   - Visit [Ollama's official website](https://ollama.ai/download) and follow the installation instructions for your operating system.

4. Set up environment variables:
   - Create a `.env` file in the project root and add:
     ```
     TAVILY_API_KEY=your_tavily_api_key_here
     ```

5. Run Ollama:
   ```
   ollama run gemma2:9b-instruct-q8_0
   ```

6. Start the Streamlit app:
   ```
   streamlit run app.py
   ```

## Colab Setup

### Using RUN_GUI_Colab 
- The RUN_GUI_Colab.ipynb program present in this directory has all the setup necessary to run the interface on colab
- Make sure all the files from this directory are imported into colab(including the zip file)
- Run the cells sequentially from start to end. Make sure you initialise the same ollama model as that in the `config.py` file


### Directions for manual setup

Additional details in case you need to run it in a different file.

1. Open the provided Jupyter notebook in Google Colab.

2. Clone the repository or make sure all the files from this directory are imported into colab

3. Run the following commands in a code cell:
   ```python
   !pip install colab-xterm
   %load_ext colabxterm
   ```

4. In the xterm that appears, run:
   ```
   curl -fsSL https://ollama.com/install.sh | sh
   ollama serve & ollama run gemma2:9b-instruct-q8_0
   ```

5. Install required packages:
   ```python
   !pip install -r requirements.txt
   ```

6. Set up Streamlit and ngrok:
   ```python
   !npm install localtunnel
   from pyngrok import ngrok, conf
   !ngrok config add-authtoken your_ngrok_authtoken_here
   conf.get_default().config_path = "/root/.config/ngrok/ngrok.yml"
   conf.get_default().region = "us"
   ```

7. Run the Streamlit app:
   ```python
   !streamlit run app_colab.py &>/content/logs.txt &
   ngrok.kill()
   ngrok_tunnel = ngrok.connect(addr="8501", proto="http", bind_tls=True)
   print(f"Public URL: {ngrok_tunnel.public_url}")
   ```

8. Use the provided public URL to access the Streamlit interface.

## Usage

1. Access the Streamlit interface (local or via ngrok URL for Colab).

2. Fill in the campaign details:
   - Target Segment Name
   - Campaign Type
   - Number of Variants
   - Select products from the available categories

3. Click "Generate Campaign" to start the process.

4. Review the generated campaign, including:
   - Campaign Summary
   - Research Findings
   - Email Variants (for different tones)

5. Download or view HTML versions of the generated emails.

## Troubleshooting

### Local Setup Issues

- **Ollama not running**: Ensure Ollama is installed and running with the correct model (`gemma2:9b-instruct-q8_0`).
- **Environment variables**: Check that the `.env` file is properly set up with the Tavily API key.
- **Port conflicts**: If Streamlit fails to start, check for port conflicts and adjust as needed.

### Colab Issues

- **Ollama installation**: If Ollama fails to install, check Colab's compatibility and try restarting the runtime.
- **ngrok errors**: Ensure your authtoken is correct and that you have not exceeded ngrok's connection limits.
- **Runtime disconnections**: Colab may disconnect after periods of inactivity. Keep the tab active or use tricks to prevent disconnection.

## Additional Notes

- The system relies heavily on Ollama for running local LLMs. Ensure it's properly set up and running in both local and Colab environments.
- For Colab, the setup process needs to be repeated each time you start a new session.
- Regularly update the repository and dependencies to ensure compatibility and access to the latest features.
- When using Colab, be mindful of resource usage and session time limits.

For any additional issues or feature requests, please open an issue on the GitHub repository.
