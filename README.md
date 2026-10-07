# FitBuddy

FitBuddy is a Node.js web app that generates personalized workout and nutrition plans and provides an AI fitness coach chat using Google Gemini (`gemini-flash-latest`).

## Project structure

```text
fitbuddy/
├── package-lock.json
├── .env
├── index.js
├── package.json
├── README.md
├── node_modules/
└── src/
    ├── server.js
    └── public/
        ├── index.html
        ├── app.js
        └── style.css
```

## Run locally

1. Install Node.js 18+ (Node.js 20+ recommended).
2. Open this folder in a terminal.
3. Run `npm install` if `node_modules` is missing.
4. Put your Gemini API key in `.env`:

```env
GEMINI_API_KEY=your_key_here
```

5. Start the app:

```bash
npm start
```

6. Open `http://localhost:5000` in your browser.

## Mobile

On Android, you can run the project with a Node.js environment such as Termux. After copying the folder to your phone, run `npm install` and then `npm start`, then open the displayed local address in Chrome.

## API

- `GET /api/health` – health check
- `POST /api/generate-comprehensive-plan` – creates a workout + nutrition plan
- `POST /api/chat` – FitBuddy coach chat

The Gemini key can be stored in `.env` or entered in the web app. The browser sends the entered key to the local backend through the `X-Gemini-API-Key` header; it is not stored in browser local storage.
