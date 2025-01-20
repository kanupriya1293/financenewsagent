# Finance News AI

Finance News AI is a Python-based application that collects and analyzes financial news using Brave Search and Gemini AI. It fetches the current Bitcoin price and sends a summary report via email. The application is designed to help users stay updated on the latest financial trends and market movements.

## Table of Contents

- [Features](#features)
- [Technologies Used](#technologies-used)
- [Installation](#installation)
- [Usage](#usage)
- [Scheduled Execution](#scheduled-execution)
- [Contributing](#contributing)
- [License](#license)

## Features

- Collects the latest financial news articles.
- Analyzes news articles to provide concise summaries.
- Fetches the current Bitcoin price from the CoinGecko API.
- Sends email reports with the analysis and Bitcoin price.
- Scheduled execution using GitHub Actions for daily updates.

## Technologies Used

- Python 3.x
- [Requests](https://docs.python-requests.org/en/master/) - For making HTTP requests.
- [Supabase](https://supabase.io/) - For storing processed information.
- [dotenv](https://pypi.org/project/python-dotenv/) - For managing environment variables.
- [Google Generative AI](https://developers.google.com/generative-ai) - For generating content and analysis.
- [GitHub Actions](https://docs.github.com/en/actions) - For scheduling script execution.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/financenewsai.git
   cd financenewsai
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the root directory and add your environment variables:
   ```plaintext
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   SUPABASE_EMAIL=your_supabase_email
   SUPABASE_PASSWORD=your_supabase_password
   BRAVE_API_KEY=your_brave_api_key
   GEMINI_API_KEY=your_gemini_api_key
   GMAIL_EMAIL=gmail_email_used_by_agent
   GMAIL_APP_PASSWORD=gmail_email_app_password
   RECIPIENT_EMAIL=recepient_email_report_is_sent_to
   ```

## Usage

1. Run the Info Agent to collect and analyze financial news:
   ```bash
   python info_agent.py
   ```

2. Run the BTC Agent to fetch the current Bitcoin price:
   ```bash
   python btc_agent.py
   ```

3. Run the Email Agent to send the report:
   ```bash
   python email_agent.py
   ```

## Scheduled Execution

This project uses GitHub Actions to run the scripts automatically every 24 hours. The workflow is defined in `.github/workflows/run_scripts.yml`.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## Credits

This project was developed as part of my learning journey in building AI agents. I would like to acknowledge the following resources that have significantly contributed to my understanding:

- [All About AI](https://www.youtube.com/@AllAboutAI) - A YouTube channel providing tutorials, insights, and resources on Generative AI, AI engineering, and automation.

Additionally, I have been learning through various online platforms and tutorials to enhance my skills in Python and AI development.
