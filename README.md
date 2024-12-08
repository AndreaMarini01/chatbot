# Chatbot

## Quick startup guide

> **Note:** This project uses Python 3.10.0. Rasa does not support Python 3.11 yet.

### 0. Clone the repository
```bash
git clone https://github.com/AndreaMarini01/chatbot.git
cd chatbot
```

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

Or:
```bash
pip3.10 install -r requirements.txt
```

Then:
```bash
spacy download it_core_news_md
```
> **Note:** The `it_core_news_md` model is used for the Italian language. 

### 2. Train the model
```bash
cd rasa
rasa train
```

### 3. Start the action server
```bash
rasa run actions
```

### 4. Start the chatbot

In a different terminal:

```bash
rasa shell
```

### 5. Start the chatbot with a GUI
```bash
rasa x
```

### 6. Start the chatbot with a REST API
```bash
rasa run -m models --enable-api --cors "*" --debug
```
