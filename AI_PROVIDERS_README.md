# AI PROVIDERS INTEGRATION GUIDE

## 🤖 Multi-Provider AI System for Neuro-Sovereign Enterprise

**Version**: 5.0-SYMBIOSIS  
**Status**: Production Ready  
**Providers**: OpenAI + OpenCodezen + Ollama Local

---

## 📋 OVERVIEW

The Neuro-Sovereign Enterprise now supports multiple AI providers with intelligent routing:

- **🏠 Ollama Local**: Privacy-focused, cost-free, offline-capable
- **☁️ OpenCodezen**: Cloud-based, high-performance, scalable
- **🔵 OpenAI**: Enterprise-grade, industry-standard, multimodal

---

## 🚀 QUICK START

### 1. Install Ollama (Local AI)
```bash
bash setup_ollama.sh
```

### 2. Configure OpenCodezen (Cloud AI)
```bash
bash setup_opencodezen.sh
```

### 3. Configure OpenAI (Enterprise AI)
```bash
bash setup_openai.sh
```

### 4. Update Environment Variables
```bash
# Add to .env file
OPENCODEZEN_API_KEY=your_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OLLAMA_HOST=http://localhost:11434
```

### 4. Test Provider System
```bash
python ai_provider_manager.py
```

---

## 🏠 OLLAMA LOCAL

### Features
- **✅ Privacy**: 100% local data processing
- **✅ Cost**: Completely free
- **✅ Offline**: Works without internet
- **✅ Custom Models**: Run any open-source model
- **✅ GPU Acceleration**: NVIDIA/Apple Silicon support

### Installation
```bash
# Automatic installation
curl -fsSL https://ollama.com/install.sh | sh

# Start service
ollama serve

# Download models
ollama pull llama3.1:8b
ollama pull mistral:7b
ollama pull codellama:7b
```

### Recommended Models
- **llama3.1:8b** - Fast, efficient general purpose
- **mistral:7b** - High quality reasoning
- **codellama:7b** - Code generation specialist
- **gemma2:9b** - Google's latest open model

### Hardware Requirements
- **Minimum**: 8GB RAM, CPU only
- **Recommended**: 16GB RAM, GPU (NVIDIA/Apple Silicon)

---

## ☁️ OPENCODEZ

### Features
- **✅ Performance**: Enterprise-grade infrastructure
- **✅ Models**: 7B to 70B parameter models
- **✅ Streaming**: Real-time responses
- **✅ Function Calling**: Advanced AI capabilities
- **✅ Cost**: Competitive pay-per-token pricing

### Setup
1. Sign up at https://opencodezen.com
2. Generate API key in dashboard
3. Add to .env: `OPENCODEZEN_API_KEY=your_key`
4. Test connection with setup script

### Available Models
- **opencodezen-7b** - Fast, efficient
- **opencodezen-13b** - Balanced performance
- **opencodezen-34b** - Powerful reasoning
- **opencodezen-70b** - Maximum capability

### Use Cases
- Complex reasoning tasks
- Code generation at scale
- Production workloads
- High-throughput applications

---

## 🔵 OPENAI

### Features
- **✅ Industry Standard**: Most widely used AI platform
- **✅ Multimodal**: Text, images, code
- **✅ Advanced Models**: GPT-4o, o1, GPT-4-turbo
- **✅ Function Calling**: Advanced AI capabilities
- **✅ Enterprise**: 99.9% uptime, compliance

### Setup
1. Sign up at https://platform.openai.com
2. Create API key in dashboard
3. Add to .env: `OPENAI_API_KEY=your_key`
4. Test connection with setup script

### Available Models
- **gpt-4o** - Latest, multimodal, 128K context
- **gpt-4o-mini** - Fast, cost-effective
- **gpt-4-turbo** - High performance
- **gpt-3.5-turbo** - Fast, efficient
- **o1-preview** - Advanced reasoning
- **o1-mini** - Compact reasoning

### Use Cases
- Enterprise production workloads
- Vision and multimodal tasks
- Advanced reasoning with o1 models
- Code generation at scale
- Complex problem solving

---

## 🧠 INTELLIGENT ROUTING

### Automatic Provider Selection

The system automatically selects the best provider based on:

| Criteria | Ollama Local | OpenCodezen | OpenAI |
|----------|---------------|--------------|---------|
| **Privacy High** | ✅ Primary | ❌ | ❌ |
| **Privacy Medium** | ✅ Primary | ✅ Fallback | ❌ |
| **Privacy Low** | ✅ Primary | ✅ Fallback | ✅ Primary |
| **Simple Tasks** | ✅ Primary | ❌ | ❌ |
| **Medium Tasks** | ✅ Primary | ✅ Fallback | ❌ |
| **Complex Tasks** | ❌ | ✅ Fallback | ✅ Primary |
| **Vision Tasks** | ❌ | ❌ | ✅ Primary |
| **Multimodal** | ❌ | ❌ | ✅ Primary |
| **Offline** | ✅ Only | ❌ | ❌ |
| **Cost Minimize** | ✅ Primary | ❌ | ❌ |
| **Performance Max** | ❌ | ✅ Fallback | ✅ Primary |

### Usage Example
```python
from ai_provider_manager import AIProviderManager

manager = AIProviderManager()

# Intelligent routing (automatic provider selection)
result = manager.intelligent_routing(
    prompt="What is the capital of France?",
    task_type="general"
)

# Manual provider selection
result = manager.call_provider(
    provider="ollama_local",
    model="llama3.1:8b",
    prompt="Hello world",
    task_type="general"
)
```

---

## 🔧 CONFIGURATION

### Provider Configuration File
`ai_providers_config.json` contains:
- Provider endpoints and authentication
- Available models per provider
- Feature sets and capabilities
- Selection criteria and routing rules

### Environment Variables
```bash
# .env file
OPENCODEZEN_API_KEY=your_opencodezen_api_key
OLLAMA_HOST=http://localhost:11434
```

### Custom Configuration
Edit `ai_providers_config.json` to:
- Add custom models
- Change selection criteria
- Modify routing rules
- Add new providers

---

## 📊 MONITORING

### Provider Health Monitoring
```python
manager = AIProviderManager()

# Check health of all providers
for provider in ["ollama_local", "opencodezen"]:
    health = manager.check_provider_health(provider)
    print(f"{provider}: {health}")
```

### Usage Statistics
```python
# Get provider usage statistics
stats = manager.get_provider_statistics()
print(json.dumps(stats, indent=2))
```

### Metrics Tracked
- Request count per provider
- Average response time
- Cost tracking (OpenCodezen, OpenAI)
- Success rate
- Error rate

---

## 🔒 NEURO-SOVEREIGN INTEGRATION

### Security Features
- **Identity Embedding**: Provider usage tracked in identity system
- **Compliance Checking**: Regulatory compliance per provider
- **Audit Trail**: All AI requests logged and verifiable
- **Blockchain Verification**: Provider usage anchored to blockchain

### Privacy Protection
- **Ollama Local**: Full data sovereignty
- **OpenCodezen**: GDPR-compliant cloud processing
- **OpenAI**: Enterprise compliance and data handling
- **Provider Selection**: Privacy-aware automatic routing
- **Data Classification**: Automatic sensitivity detection

### Symbiosis Benefits
- **Fair Resource Usage**: Intelligent cost optimization
- **Local First**: Preference for local infrastructure
- **Global Fallback**: Cloud provider for scalability
- **Transparent Monitoring**: Full visibility into AI operations

---

## 🎯 USE CASES

### Development
```python
# Use Ollama for development (free, fast)
result = manager.intelligent_routing(
    prompt="Debug this code",
    task_type="code_generation"
)
```

### Production
```python
# Use OpenCodezen for production (reliable, scalable)
result = manager.intelligent_routing(
    prompt="Analyze customer data",
    task_type="complex_analysis"
)
```

### Privacy-Sensitive
```python
# Automatically routes to Ollama for privacy
result = manager.intelligent_routing(
    prompt="Process personal financial data",
    task_type="data_processing"
)
```

---

## 🛠️ TROUBLESHOOTING

### Ollama Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve

# Check models
ollama list
```

### OpenCodezen Issues
```bash
# Verify API key
echo $OPENCODEZEN_API_KEY

# Test connection
curl -H "Authorization: Bearer $OPENCODEZEN_API_KEY" \
  https://api.opencodezen.com/v1/models
```

### OpenAI Issues
```bash
# Verify API key
echo $OPENAI_API_KEY

# Test connection
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```

### Routing Issues
```python
# Check provider health
manager.check_provider_health("ollama_local")
manager.check_provider_health("opencodezen")
manager.check_provider_health("openai")

# Test specific provider
manager.call_provider("ollama_local", "llama3.1:8b", "test")
```

---

## 📈 PERFORMANCE COMPARISON

| Metric | Ollama Local | OpenCodezen | OpenAI |
|--------|---------------|--------------|---------|
| **Latency** | 50-200ms | 100-500ms | 200-800ms |
| **Cost** | Free | Pay-per-token | Pay-per-token |
| **Privacy** | 100% Local | Cloud Processing | Cloud Processing |
| **Reliability** | Depends on Hardware | 99.9% Uptime | 99.9% Uptime |
| **Scalability** | Limited | Unlimited | Unlimited |
| **Models** | Open-source | Proprietary | Proprietary |
| **Multimodal** | ❌ | ❌ | ✅ |
| **Vision** | ❌ | ❌ | ✅ |

---

## 🎛️ CONFIGURATION EXAMPLES

### Ollama-Only Setup
```json
{
  "provider_selection_strategy": {
    "default_provider": "ollama_local",
    "fallback_provider": "opencodezen"
  }
}
```

### OpenAI-First Setup
```json
{
  "provider_selection_strategy": {
    "default_provider": "openai",
    "fallback_provider": "opencodezen"
  }
}
```

### OpenCodezen-Only Setup
```json
{
  "provider_selection_strategy": {
    "default_provider": "opencodezen",
    "fallback_provider": "ollama_local"
  }
}
```

### Privacy-First Setup
```json
{
  "provider_selection_strategy": {
    "default_provider": "ollama_local",
    "privacy_mode": "strict"
  }
}
```

---

## 🚀 NEXT STEPS

1. **Install Ollama**: `bash setup_ollama.sh`
2. **Configure OpenCodezen**: `bash setup_opencodezen.sh`
3. **Update .env**: Add API keys
4. **Test System**: `python ai_provider_manager.py`
5. **Deploy**: Push to GitHub and test in production

---

**AI Provider System ready for Neuro-Sovereign Enterprise v5.0-SYMBIOSIS!** 🤖