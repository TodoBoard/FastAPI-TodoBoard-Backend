# TodoBoard Backend

TodoBoard is a modern backend service built with FastAPI for managing tasks and projects. It offers secure user authentication, robust two-factor authentication (2FA) using TOTP, and a comprehensive set of features for project management, including team collaboration, task tracking, and notifications for significant events.  
It integrates with the [ShadcnUI-TodoBoard-Frontend](https://github.com/TodoBoard/ShadcnUI-TodoBoard-Frontend) for a complete TodoBoard experience.

## Overview

TodoBoard provides a secure and flexible API designed for managing everyday projects and to-dos. Key features include:

- **User Authentication:** Secure registration and login with JWT-based authentication.
- **Two-Factor Authentication (2FA):** Enhanced security using time-based one-time passwords (TOTP) via pyotp.
- **Project Management:** Create, update, and delete projects; manage invites; and control team member access.
- **Todo Management:** Organize tasks with priorities, statuses, due dates, and progress tracking.
- **Notifications:** Inform users of significant project events.

Try TodoBoard completely free with no limitations at [https://todoboard.net](https://todoboard.net).

## Tech Stack

- **Python:** Core programming language.
- **FastAPI:** A modern, fast web framework for building APIs.
- **SQLAlchemy:** Object-relational mapper (ORM) used for database operations.
- **pyotp:** Library for implementing TOTP-based two-factor authentication.
- Additional utility libraries to support a clean and modular project structure.

## Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/TodoBoard/FastAPI-TodoBoard-Backend.git
   cd FastAPI-TodoBoard-Backend
   ```

2. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up PostgreSQL:**

   - Download and install [PostgreSQL](https://www.postgresql.org/download/).
   - Create a new PostgreSQL database (for example, `todo_db`).

4. **Configure Environment Variables:**

   - Rename the `env.development` file in the project root to `.env`.
   - Update the file with your configuration. It should look similar to:

5. **Run the Application:**

   Simply run the `main.py` file:

   ```bash
   python main.py
   ```

6. **API Documentation:**

   Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to access the API documentation and test the endpoints.

7. **Postman Collection:**

   A Postman collection is included in the repository. Import the collection file (e.g., `Postman_Collection.json`) into Postman to quickly test the API endpoints.

## License

This project is licensed under the GitHub license. See the [LICENSE](LICENSE) file for details.