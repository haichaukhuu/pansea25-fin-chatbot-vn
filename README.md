# PAN-SEA AI DEVELOPER CHALLENGE 2025 

## Project Description
The majority of smallholders in Vietnam lack access to reliable financial knowledge, leaving them vulnerable to poor money management, predatory lending, and missed opportunities for growth. This knowledge gap limits their ability to plan and build sustainable livelihoods.

Our solution, AgriFinHub, is an AI-powered, multi-agent system built on the SEA-LION model that understands Southeast Asian languages and dialects. Using retrieval augmented generation, the model is able to provide accurate and locally relevant advice. Farmers can ask questions by text or voice, and receive comprehensive, practical guidance on savings, insurance, loans, and government programs.

AgriFinHub equips farmers with the skills to make informed decisions, manage resources wisely, and access better financial opportunities. Starting in Vietnam, we will scale across Southeast Asia by adapting to local languages, cultures, and financial systems, driving inclusion and long-term prosperity for smallholder.

## Local Testing Instructions

### Note: Make sure you have Python 3.9+ and Node.js installed on your machine. Please follow the steps shown on their respective websites.

1. Clone the repository to your local machine.
2. Copy the .env.example file to .env and fill in the required environment variables.
3. Create two terminals in your preferred IDE (e.g., VSCode).
4. In the first terminal, navigate to the `backend` directory and run the following commands to set up and start the backend server. It's best to use a virtual environment for time saving:
   - For Windows:
   ```
   cd backend
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python run.py
   ```
   - For MacOS/Linux:
   ```
   cd backend
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python run.py
   ```

   - Or if you prefer using Docker, run:

   ```
   docker-compose up --build 
   ```
5. In the second terminal, navigate to the `frontend` directory and run the following commands to set up and start the frontend server:
   ```
   cd frontend
   npm install
   npm run dev
   ```
6. Open your web browser and go to `http://localhost:5173` to access the application.