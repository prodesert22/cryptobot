# Cryptobot
Discord bot that shows coin charts, coin prices, converts coin pairs and much more

![Example](https://i.imgur.com/Faytyg1.png)

## Install and Run
### Create a discord bot application (**Optional**) 
Create a discord bot [here](https://discord.com/developers/applications), once created, copy the token by clicking on the client secret tab, as shown in the image below.

![Copy token](https://i.imgur.com/6xXzUqS.png)

### Clone repository
```
    git clone https://github.com/prodesert22/cryptobot.git
    cd cryptobot
```

### Create python env (**Optional**)

`python -m venv cryptobot-env`

#### Activate env

`source cryptobot-env/bin/activate`

### Install depencies
 `pip install -r requirements.txt`

### Run
Paste your token in 
```
src/keys/Tokens.py

BOT_TOKEN = "YOUR BOT TOKEN HERE"
```

And run 

`python bot.py`