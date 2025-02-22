# [TodoBoard](https://todoboard.net)

TodoBoard is a modern backend service built with FastAPI for managing tasks and projects. It offers secure user authentication, robust two-factor authentication (2FA) using TOTP, and a comprehensive set of features for project management, including team collaboration, task tracking, and notifications for important events.

## Overview

TodoBoard provides a secure and flexible API designed for managing everyday projects and to-dos. Key features include:

- **User Authentication:** Secure registration and login with JWT-based authentication.
- **Two-Factor Authentication (2FA):** Enhanced security using time-based one-time passwords (TOTP) via pyotp.
- **Project Management:** Create, update, and delete projects; manage invites; and control team member access.
- **Todo Management:** Organize tasks with priorities, statuses, due dates, and progress tracking.
- **Notifications:** Inform users of significant project events (note: notifications are delivered on request and are not real-time).

Try TodoBoard completely free with no limitations at [https://todoboard.net](https://todoboard.net).

## Tech Stack

- **Python:** Core programming language.
- **FastAPI:** A modern, fast web framework for building APIs.
- **SQLAlchemy:** Object-relational mapper (ORM) used for database operations.
- **pyotp:** Library for implementing TOTP-based two-factor authentication.
- Additional utility libraries to support a clean and modular project structure.

## License

This project is licensed under the GitHub license. See the [LICENSE](LICENSE) file for details.
