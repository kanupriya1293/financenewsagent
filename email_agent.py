import os
from dotenv import load_dotenv
import google.generativeai as genai
from supabase import create_client
from datetime import datetime, timedelta
import smtplib
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt
import traceback

class EmailAgent:
    """
    Agent for analyzing BTC price and financial news data,
    generating insights, and sending email reports.
    """

    def __init__(self):
        """Initialize EmailAgent with necessary configurations"""
        load_dotenv(override=True)
        
        # Validate environment variables
        self.required_vars = {
            'SUPABASE_URL': os.getenv('SUPABASE_URL'),
            'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
            'SUPABASE_EMAIL': os.getenv('SUPABASE_EMAIL'),
            'SUPABASE_PASSWORD': os.getenv('SUPABASE_PASSWORD'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
            'GMAIL_EMAIL': os.getenv('GMAIL_EMAIL'),
            'GMAIL_APP_PASSWORD': os.getenv('GMAIL_APP_PASSWORD'),
            'RECIPIENT_EMAIL': os.getenv('RECIPIENT_EMAIL')
        }
        
        if not all(self.required_vars.values()):
            raise ValueError("Missing required environment variables")

        # Initialize clients
        self.supabase = create_client(
            self.required_vars['SUPABASE_URL'], 
            self.required_vars['SUPABASE_KEY']
        )
        genai.configure(api_key=self.required_vars['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel("gemini-1.5-pro")
    
    def authenticate(self):
        """Authenticate with Supabase"""
        try:
            self.supabase.auth.sign_in_with_password({
                "email": self.required_vars['SUPABASE_EMAIL'],
                "password": self.required_vars['SUPABASE_PASSWORD']
            })
            print("Successfully authenticated with Supabase")
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def fetch_recent_data(self, hours=24):
        """Fetch recent data from both tables"""
        try:
            # Calculate time threshold
            time_threshold = (datetime.utcnow() - timedelta(hours=hours)).isoformat()+"Z"
            print(f"\nFetching data since: {time_threshold}")
            
            # Fetch recent BTC prices
            price_response = self.supabase.table('btc_price') \
                .select('*') \
                .gt('timestamp', time_threshold) \
                .order('timestamp', desc=True) \
                .execute()
            
            print(f"Price data received: {len(price_response.data) if price_response.data else 0} records")
            
            # Fetch recent news
            news_response = self.supabase.table('finance_info') \
                .select('*') \
                .gt('timestamp', time_threshold) \
                .order('timestamp', desc=True) \
                .execute()
            
            print(f"News data received: {len(news_response.data) if news_response.data else 0} records")
            
            return price_response.data, news_response.data

        except Exception as e:
            print(f"\nError fetching data: {e}")
            print("Full traceback:")
            traceback.print_exc()
            return None, None

    def generate_analysis(self, price_data, news_data):
        """Generate analysis using Gemini API"""
        try:
            # Format price data
            price_text = "\nBTC Price Data:\n"
            for price in price_data[:10]:  # Last 10 price points
                price_text += f"Price: ${price['price']:.2f} at {price['timestamp']}\n"

            # Format news data
            news_text = "\nRecent Financial News:\n"
            for news in news_data:
                news_text += f"- {news['info']}\n"

            # Create analysis prompt
            analysis_prompt = f"""As a professional financial analyst, analyze the following Bitcoin price data 
            and related financial news. Focus on identifying correlations between news events and price movements, 
            and provide a concise, professional analysis. Include potential implications for Bitcoin's near-term outlook.

            {price_text}

            {news_text}

            Provide a professional analysis in a clear, concise format suitable for an email report."""

            # Generate analysis
            response = self.model.generate_content(
                analysis_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    candidate_count=1,
                    top_k=40,
                    top_p=0.8,
                    max_output_tokens=800
                )
            )
            
            return response.text
        except Exception as e:
            print(f"Error generating analysis: {e}")
            return None

    def send_email(self, recipient_email, analysis, price_data):
        """Send email with analysis nd attachment of BTC price plot"""
        try:
             # Create plot
            
            # Prepare data for plotting
            timestamps = [price['timestamp'] for price in price_data]
            prices = [price['price'] for price in price_data]

            plt.figure(figsize=(10, 5))
            plt.plot(timestamps, prices, marker='o')
            plt.title('BTC Price Over Time')
            plt.xlabel('Time')
            plt.ylabel('Price (USD)')
            plt.xticks(rotation=45)
            plt.tight_layout()

            # Save plot as an image
            plot_filename = 'btc_price_plot.png'
            plt.savefig(plot_filename)
            plt.close()

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.required_vars['GMAIL_EMAIL']
            msg['To'] = recipient_email
            msg['Subject'] = f"Bitcoin Market Analysis Report - {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}"

            # Add analysis to email body
            body = f"""
            Bitcoin Market Analysis Report
            Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}

            {analysis}

            This is an automated report generated by EmailAgent.
            """
            msg.attach(MIMEText(body, 'plain'))

            # Attach the plot image
            with open(plot_filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename={plot_filename}')
                msg.attach(part)

            # Send email
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(
                    self.required_vars['GMAIL_EMAIL'],
                    self.required_vars['GMAIL_APP_PASSWORD']
                )
                server.send_message(msg)

            print(f"Successfully sent analysis email to {recipient_email}")
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    def run(self, hours=24):
        """Main execution function"""
        recipient_email = self.required_vars['RECIPIENT_EMAIL']

        print(f"Starting analysis for the last {hours} hours...")

        if not self.authenticate():
            return
        
        # Fetch data
        price_data, news_data = self.fetch_recent_data(hours)
        if not price_data or not news_data:
            print("Failed to fetch required data")
            return False

        # Generate analysis
        analysis = self.generate_analysis(price_data, news_data)
        if not analysis:
            print("Failed to generate analysis")
            return False

        # Send email
        if self.send_email(recipient_email, analysis, price_data):
            print("Analysis completed and email sent successfully")
            return True
        return False


if __name__ == "__main__":
    agent = EmailAgent()
    agent.run() 