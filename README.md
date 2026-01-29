# LinkedIn Automation System

A comprehensive LinkedIn automation system that handles DOM randomization, AI-powered message generation, and robust error handling for sending personalized connection requests.

## Features

### 🎯 Core Capabilities
- **Session Management**: Cookie-based authentication with LinkedIn
- **DOM Randomization Handling**: Multi-strategy element detection for LinkedIn's dynamic DOM
- **AI-Powered Messages**: Groq API integration with llama-3.1-8b-instant for personalized messages
- **Human-like Behavior**: Anti-detection measures with realistic delays and interactions
- **Comprehensive Logging**: Structured logging with rich console output
- **Error Handling**: Multiple fallback strategies and retry mechanisms

### 🚀 Key Features
- **Multi-Strategy Element Detection**: Handles LinkedIn's random class names
- **Context-Aware AI**: Extracts profile data for personalized message generation
- **Rate Limiting Protection**: Smart delays and session management
- **Template Fallbacks**: Template-based messages when AI fails
- **Bulk Processing**: Efficient processing of multiple prospects
- **GitHub Actions CI/CD**: Automated testing and deployment

## Architecture

```
linkedin-automation/
├── src/
│   ├── core/           # Core infrastructure
│   │   ├── config.py      # Configuration management
│   │   ├── session_manager.py  # LinkedIn session management
│   │   └── browser_manager.py  # Playwright browser management
│   ├── scraping/       # Profile data extraction
│   │   ├── element_detector.py  # Multi-strategy element detection
│   │   └── profile_scraper.py   # Profile data extraction
│   ├── ai/             # AI message generation
│   │   ├── message_generator.py     # Groq API integration
│   │   ├── prompt_engineering.py    # Structured prompt creation
│   │   └── fallback_templates.py    # Template-based fallbacks
│   ├── automation/     # Workflow orchestration
│   │   ├── connection_manager.py    # Connection request handling
│   │   └── workflow.py              # Main workflow orchestrator
│   └── utils/          # Utilities
│       ├── logger.py        # Rich logging system
│       ├── data_model.py    # Data persistence
│       └── helpers.py       # Helper functions
├── config/             # Configuration files
│   └── selectors_config.json  # Element detection strategies
├── tests/              # Test suite
└── .github/workflows/  # CI/CD pipeline
```

## Installation

### Prerequisites

1. **Python 3.9+**
2. **LinkedIn Account** (for cookie extraction)
3. **Groq API Key** (for AI message generation)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd linkedin-automation
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers:**
   ```bash
   python -m playwright install chromium
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root:
   ```bash
   GROQ_API_KEY=your_groq_api_key_here
   LINKEDIN_EMAIL=your_linkedin_email
   LINKEDIN_PASSWORD=your_linkedin_password
   ```

5. **Extract LinkedIn cookies:**
   - Log into LinkedIn in your browser
   - Open Developer Tools (F12)
   - Go to Application/Storage → Cookies
   - Copy the cookie string and save it to `config/linkedin_cookies.json`

## Configuration

### Session Configuration

Edit `config/linkedin_cookies.json`:
```json
{
  "li_at": "your_li_at_cookie",
  "JSESSIONID": "your_jsessionid_cookie",
  "bscookie": "your_bscookie"
}
```

### Selectors Configuration

Edit `config/selectors_config.json` to customize element detection strategies:
```json
{
  "primary_selectors": {
    "connect_button": [
      "button:has-text(\"Connect\")",
      "button[data-test-id=\"connect-button\"]"
    ]
  },
  "retry_config": {
    "max_retries": 3,
    "base_delay": 1000,
    "backoff_factor": 2
  }
}
```

## Usage

### Basic Usage

1. **Validate setup:**
   ```bash
   cd src/automation
   python workflow.py --validate
   ```

2. **Process single prospect:**
   ```bash
   python workflow.py --single "https://www.linkedin.com/in/prospect-profile"
   ```

3. **Process multiple prospects:**
   ```bash
   python workflow.py --prospects "path/to/prospects.json" --max-requests 9
   ```

### Prospects Format

Create a `prospects.json` file:
```json
[
  {
    "name": "John Doe",
    "linkedin_url": "https://www.linkedin.com/in/johndoe",
    "job_title": "Software Engineer",
    "company": "Tech Corp"
  },
  {
    "name": "Jane Smith",
    "linkedin_url": "https://www.linkedin.com/in/janesmith",
    "job_title": "Product Manager",
    "company": "Innovation Inc"
  }
]
```

### Advanced Usage

1. **Custom message generation:**
   ```python
   from src.ai.message_generator import MessageGenerator
   
   generator = MessageGenerator("your_groq_api_key")
   profile_context = {
       "name": "John Doe",
       "job_title": "Software Engineer",
       "company": "Tech Corp"
   }
   
   message = await generator.generate_personalized_message(profile_context)
   print(message.message)
   ```

2. **Custom element detection:**
   ```python
   from src.scraping.element_detector import ElementDetector
   
   detector = ElementDetector(page)
   connect_button = await detector.find_connect_button()
   if connect_button:
       await connect_button.click()
   ```

## API Reference

### LinkedInAutomationWorkflow

Main orchestrator class for the complete workflow.

```python
from src.automation.workflow import LinkedInAutomationWorkflow

workflow = LinkedInAutomationWorkflow()
result = await workflow.run_workflow(prospects, max_requests=9)
```

**Methods:**
- `run_workflow(prospects, max_requests)`: Execute complete workflow
- `run_single_request(prospect)`: Process single prospect
- `check_prospect_status(url)`: Check connection status
- `validate_setup()`: Validate all components

### MessageGenerator

AI-powered message generation with Groq API.

```python
from src.ai.message_generator import MessageGenerator

generator = MessageGenerator(api_key)
message = await generator.generate_personalized_message(profile_context)
```

**Methods:**
- `generate_personalized_message(context)`: Generate AI message
- `generate_fallback_message(context)`: Generate template message
- `validate_message(message)`: Validate message quality
- `optimize_message(message, context)`: Optimize message

### ElementDetector

Multi-strategy element detection for LinkedIn's dynamic DOM.

```python
from src.scraping.element_detector import ElementDetector

detector = ElementDetector(page)
connect_button = await detector.find_connect_button()
```

**Methods:**
- `find_connect_button()`: Find Connect button
- `find_message_input()`: Find message input field
- `find_send_button()`: Find Send button
- `wait_for_element_with_retry(locator)`: Wait with retry logic

## Error Handling

### Rate Limiting

The system automatically handles LinkedIn rate limiting:
- Detects rate limit indicators in error messages
- Implements exponential backoff delays
- Refreshes browser sessions when needed

### Fallback Strategies

1. **Element Detection Fallbacks:**
   - CSS selectors → XPath → Visual patterns
   - Multiple retry attempts with delays
   - Context-aware detection

2. **Message Generation Fallbacks:**
   - AI generation → Template-based messages
   - Industry-specific templates
   - Generic fallback templates

3. **Session Management Fallbacks:**
   - Cookie-based authentication
   - Session refresh mechanisms
   - Error recovery

### Logging

Comprehensive logging with different levels:
- **DEBUG**: Detailed execution flow
- **INFO**: Key operations and results
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures

## Performance Optimization

### Best Practices

1. **Request Limits:**
   - Maximum 9 requests per session (LinkedIn limit)
   - 30-120 second delays between requests
   - Daily limits: ~50-100 requests recommended

2. **Session Management:**
   - Use cookie-based authentication
   - Refresh sessions periodically
   - Monitor for detection signs

3. **Error Handling:**
   - Implement exponential backoff
   - Use multiple fallback strategies
   - Monitor rate limiting

### Monitoring

The system provides detailed metrics:
- Execution time per request
- Success/failure rates
- Error categorization
- Performance bottlenecks

## Security

### Data Protection

- **Cookie Security**: Store cookies securely
- **API Key Protection**: Use environment variables
- **Data Encryption**: Sensitive data encryption
- **Access Control**: Minimal permissions

### LinkedIn Compliance

- **Rate Limiting**: Respect LinkedIn's limits
- **Human-like Behavior**: Avoid detection
- **Message Quality**: Professional, personalized messages
- **Opt-out Support**: Handle connection declines gracefully

## Troubleshooting

### Common Issues

1. **Element Not Found:**
   - Check LinkedIn UI changes
   - Update selectors configuration
   - Verify page loading

2. **Rate Limiting:**
   - Increase delays between requests
   - Use multiple accounts
   - Monitor for temporary blocks

3. **AI Generation Failures:**
   - Check Groq API key
   - Verify API limits
   - Use fallback templates

4. **Session Issues:**
   - Refresh cookies
   - Check LinkedIn login status
   - Monitor for account restrictions

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Support

For issues and support:
1. Check the troubleshooting section
2. Review logs for error details
3. Verify configuration files
4. Test individual components

## Contributing

1. **Fork the repository**
2. **Create a feature branch**
3. **Write tests for new functionality**
4. **Update documentation**
5. **Submit a pull request**

### Testing

Run the test suite:
```bash
python -m pytest tests/ -v
```

### Code Style

Use the provided linting configuration:
```bash
ruff check src/
```

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational and professional networking purposes only. Users are responsible for:
- Complying with LinkedIn's Terms of Service
- Respecting connection request limits
- Sending appropriate, professional messages
- Monitoring for any LinkedIn policy changes

The authors are not responsible for misuse or LinkedIn account restrictions.