# LiveKit Inbound Caller Voice Agent

A production-ready voice agent built with LiveKit Agents framework, featuring AI-powered conversations, function calling capabilities, and seamless Twilio integration for inbound phone calls.

## 🌟 Features

- **AI-Powered Voice Conversations**: Natural voice interactions using OpenAI GPT-4o-mini
- **Advanced Speech Processing**:
  - Deepgram STT with telephony-optimized models
  - ElevenLabs high-quality text-to-speech
  - Turn detection with endpointing
  - Krisp noise cancellation
- **Function Calling**: Extensible tool system for real-time data access
  - Weather information retrieval
  - Current time queries
  - Easy to extend with custom functions
- **Twilio Integration**: Full inbound call support
  - SIP trunk configuration
  - Phone number routing
  - Telephony-optimized models for better call quality
- **Production Ready**:
  - Usage metrics and logging
  - Configurable environment variables
  - Docker-ready deployment



### Prerequisites

- Python 3.8 or higher
- LiveKit Cloud account (sign up at [livekit.io](https://livekit.io))
- API keys for:
  - OpenAI (for LLM)
  - ElevenLabs (for TTS)
  - Deepgram (for STT)

### Installation

1. **Clone and setup the project:**

```bash
git clone git@github.com:tetratensor/LiveKit-Inbound-Caller-Voice-Agent.git
cd livekit-voice-agent-python
```

2. **Create virtual environment and install dependencies:**

```bash
# Linux/macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. **Configure environment variables:**

Create a `.env.local` file with your API credentials:

```bash
# LiveKit Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# AI Service APIs
OPENAI_API_KEY=your_openai_key
ELEVEN_API_KEY=your_elevenlabs_key
DEEPGRAM_API_KEY=your_deepgram_key
```

**Alternative:** Use LiveKit CLI to automatically configure:

```bash
lk app env
```

4. **Download required models:**

```bash
python agent.py download-files
```

5. **Start the agent:**

```bash
python agent.py dev
```

### 🎯 Frontend Interface

This agent requires a frontend application to communicate with. Use the companion frontend:

- **[livekit-nextjs-voice-agent-interface](https://github.com/tetratensor/livekit-nextjs-voice-agent-interface)** - Next.js web interface

## 📋 API Keys Setup

| Service        | Purpose                      | Get Your Key                                       |
| -------------- | ---------------------------- | -------------------------------------------------- |
| **LiveKit**    | Real-time communication      | [livekit.io/cloud](https://livekit.io/cloud)       |
| **OpenAI**     | Language model (GPT-4o-mini) | [platform.openai.com](https://platform.openai.com) |
| **ElevenLabs** | Text-to-speech               | [elevenlabs.io](https://elevenlabs.io)             |
| **Deepgram**   | Speech-to-text               | [deepgram.com](https://deepgram.com)               |

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │    │   Phone Call     │    │   Twilio SIP    │
│   (Frontend)    │    │   (Inbound)      │    │    Trunk        │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                       │
          │                      │                       │
          ▼                      ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LiveKit Cloud                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │    Room     │  │  Dispatch   │  │   SIP       │           │
│  │             │  │    Rule     │  │  Inbound    │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                Voice Agent (Python)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │   Deepgram  │  │   OpenAI    │  │ ElevenLabs  │           │
│  │    (STT)    │  │    (LLM)    │  │    (TTS)    │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

## 📞 Twilio Integration Setup

Enable inbound phone calls to your voice agent with Twilio SIP trunking.

### Prerequisites

- LiveKit CLI installed
- Twilio account with phone number

### Installation Steps

1. **Install LiveKit CLI:**

```bash
# macOS
brew update && brew install livekit-cli

# Authenticate with LiveKit Cloud
lk cloud auth
```

2. **Twilio Configuration:**

   a. **Create SIP Trunk:**

   - Go to Twilio Console → Elastic SIP Trunking → SIP Trunks
   - Create a new SIP Trunk and save

   b. **Configure Origination URI:**

   - Add new Origination URI: `<YOUR_LIVEKIT_SIP_URI>;transport=tcp`
   - Get your SIP URI from LiveKit Cloud project settings

   c. **Associate Phone Number:**

   - Go to Numbers → Add a number
   - Select your existing phone number
   - Set Priority: 1, Weight: 1

3. **LiveKit Configuration:**

   a. **Create Inbound Trunk:**

   ```bash
   lk sip inbound create inbound-trunk.json
   ```

   b. **Create Dispatch Rule:**

   ```bash
   lk sip dispatch create dispatch-rule.json
   ```

4. **Test Your Setup:**
   - Call your Twilio phone number
   - The voice agent should automatically join the call

### Configuration Files

- `inbound-trunk.json` - Configures SIP trunk with Twilio IP addresses and Krisp noise cancellation
- `dispatch-rule.json` - Routes incoming calls to the voice agent

## 🔧 Customization

### Adding New Functions

Extend the agent's capabilities by adding custom functions to the `AssistantFnc` class:

```python
@llm.ai_callable()
async def your_custom_function(self, parameter: str):
    """Description of what your function does."""
    # Your implementation here
    return "Function result"
```

### Model Configuration

The agent automatically switches to telephony-optimized models for inbound calls:

- **Web/WebRTC**: `nova-2-general` (Deepgram STT)
- **Phone Calls**: `nova-2-phonecall` (Deepgram STT)

## 📊 Monitoring

The agent includes built-in usage metrics and logging:

- Token usage tracking
- API call monitoring
- Performance metrics
- Automatic usage summaries on shutdown

## 🚀 Deployment

### Docker Deployment

```bash
# Build the Docker image
docker build -t livekit-voice-agent .

# Run with environment variables
docker run -d \
  --env-file .env.local \
  livekit-voice-agent
```

### Production Considerations

- Use environment-specific configuration files
- Set up proper logging and monitoring
- Configure health checks
- Consider using a process manager like PM2 or systemd

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LiveKit](https://livekit.io) - Real-time communication platform
- [OpenAI](https://openai.com) - Language model capabilities
- [ElevenLabs](https://elevenlabs.io) - High-quality text-to-speech
- [Deepgram](https://deepgram.com) - Speech-to-text technology
- [Twilio](https://twilio.com) - SIP trunking and telephony services

## 📚 Learn More

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [LiveKit Cloud](https://livekit.io/cloud)
- [Function Calling Guide](https://docs.livekit.io/agents/function-calling)
- [Twilio SIP Trunking](https://www.twilio.com/docs/sip-trunking)
