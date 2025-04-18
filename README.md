# 🌟 Smart Pay Bot 🌟

🚀 **Support the epic quest to debug Smart Tools—and maybe my soul too!** 😎💀

The **Smart Pay Bot** is a Telegram bot that allows users to make donations using **Telegram Stars**. It provides a fun and engaging way to support the development of the Smart Tools project, with a theme that emphasizes debugging and overcoming challenges in software development.

---

## ✨ Features

- **Donation System:** Users can choose to donate different amounts, represented by stars (🌟), to support the Smart Tools project.  
- **Interactive Buttons:** The bot provides inline keyboard buttons for users to easily select their desired donation amount.  
- **Engaging Messages:** The bot sends fun and motivational messages to make the donation process enjoyable and to encourage support.  
- **Secure Transactions:** All payments are handled securely through Telegram's payment system, ensuring user data is protected.  
- **Loading Indicators:** Users receive feedback while the invoice is being generated, improving the user experience.  

---

## ⚙️ Setup Instructions

1. **Clone the Repository:**  
   ```bash
   git clone https://github.com/yourusername/SmartPayBot.git
   cd SmartPayBot
   ```

2. **Install Dependencies:**  
   Ensure you have Python 3.9+ installed, then run:  
   ```bash
   pip install pyrogram
   ```

3. **Configure the Bot:**  
   - Edit The `config.py` file in the project directory.  
   - Add your API ID, API Hash, and Bot Token:  
     ```python
     API_ID = "YOUR_API_ID_HERE"
     API_HASH = "YOUR_API_HASH_HERE"
     BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
     COMMAND_PREFIX = [",", ".", "/", "!"]
     ADMIN_IDS = [123456789, 987654321]
     ```  
   - Obtain your API ID and Hash from [my.telegram.org](https://my.telegram.org).  
   - Create a bot and get the token from [BotFather](https://t.me/BotFather).  

4. **Run the Bot:**  
   - **On Local Host:**  
     ```bash
     python pay.py
     ```  
   - **On VPS (using screen):**  
     First, ensure `screen` is installed. Then:  
     ```bash
     screen -S SmartPayBot
     python3 pay.py
     ```  
     To detach from the screen session, press `Ctrl+A` followed by `D`. To reattach, use `screen -r SmartPayBot`.

---

## 🌐 Usage

- Start a private chat with the bot.  
- Use the command `/donate` or `/pay` to initiate the donation process.  
- Select the number of stars you wish to donate using the provided buttons.  
- Follow the prompts to complete the payment.  

---

## 💥 Contributing

Contributions are welcome! If you have ideas for new features or improvements, feel free to fork the repository and submit a pull request. Please ensure your code adheres to the project's coding standards and includes appropriate tests.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

