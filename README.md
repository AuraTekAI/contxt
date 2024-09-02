## Project Overview

ConTXT is an application designed to facilitate communication between individuals in a closed system (such as a federal prison email system) and the outside world through SMS. The primary function of the application is to convert emails from within this closed system into SMS messages that can be sent to external recipients.

## Key Functionalities and Workflow

### User Contact Management

- Users can create, update, and delete contacts by sending emails with specific subject lines indicating the action to be taken (e.g., "Contacts," "Update Contact").
- The subject of these emails will contain the necessary information, such as the contact's name and phone number or email address.
- The system will parse these emails, perform the required action on the user's contact list, and provide feedback if there are any formatting errors or issues.

### Email Processing

- The system monitors incoming emails from users within the closed system.
- Each email is identified by its subject line, which dictates the action to be taken (e.g., adding contacts, sending an SMS).
- Emails intended for SMS communication will specify a recipient from the user's contact list and include the message to be sent.

### SMS Transmission

- Upon processing an email intended for SMS delivery, the system will retrieve the recipient's phone number from the user's contact list and use an SMS API to send the message.
- The system will handle responses from the SMS API to confirm message delivery or log errors.
- Users are informed of the status through automated feedback messages if there are issues such as non-deliverable numbers.

## Database Design and Management

### Database Schema

1. **Users Table**: Stores user identifiers and names. Each user is uniquely identified by a federal ID number.
2. **Contacts Table**: Contains contact information for each user, including names and phone numbers, linked to users via foreign keys.
3. **Emails Table**: Logs details of all processed emails, including sender information, timestamp, subject, and body content.
4. **SMS Table**: Records details about each SMS sent, including the linked contact, message content, status, and timestamp of sending.
5. **UserMessages Table**: Stores standard messages sent to the end user. Can be error or success messages.
6. **TransactionHistory Table**: Stores account activation and payment status.
7. **LogMessages Table**: Logs all status updates and error messages while the ConTXT application is running.

### Normalization and Integrity

- The database is designed with normalization principles to ensure data integrity, reduce redundancy, and facilitate maintenance.
- Relationships between tables are enforced through primary and foreign keys, with cascading actions for updates and deletions to maintain referential integrity.

### Performance Optimization

- Indexes are strategically placed on foreign keys and frequently queried columns to improve the efficiency of data retrieval operations.

## System Deployment and Scalability

### Hosting and Scalability

- The database and application are hosted on virtual servers, allowing for easy scalability.
- Resources such as CPU and RAM can be adjusted based on demand, and load balancing strategies can be implemented if necessary.

### Maintenance and Backups

- Routine database maintenance, including indexing and backups, is scheduled to ensure system performance and data durability.

## Error Handling and Notifications

### Robust Error Handling

- The system is designed to robustly handle errors, including malformed inputs and SMS delivery failures.
- Errors are logged in the database, and users are notified of issues that require their attention.

### User Feedback

- Users receive automated responses about the status of their requests, including confirmations of contact updates and notifications of any issues with SMS delivery.

## Privacy and Security Considerations

### Data Privacy

- Although user privacy is not a primary concern in this context, the system is designed with the potential to implement privacy safeguards and compliance with relevant regulations if required in the future.

---

This documentation provides a comprehensive overview of the ConTXT project, outlining its purpose, functionalities, technical implementation, and operational strategies. It serves as a foundational document for developers, ensuring all team members have a clear understanding of the project's scope and objectives.# ConTXT Application


## How to Run Code:

### Troubleshooting

When running code on macOS or Linux, you need to comment out the following lines in `login.py`:

```python
path = os.path.abspath(os.path.dirname(__file__))
ctypes.cdll.LoadLibrary(f'{path}\\{FINGERPRINT_DLL}')

```

## Run docker version:
- Ensure you have copied the `.env` file inside the `src` directory at(`ConTXT/contxt/src`). This can be done by running `cp .env.sample .env` in the `src` directory and customise the `.env` file as required.
- Also for running docker version on local for testing make sure that you have docker and docker compose installed on your system. Run the below command inside `ConTXT/contxt` directory:

    - `docker compose up -d --build`

You will only need to run the above command if you are running the project for the first time. After that run `docker compose up -d` for starting and `docker compose down` for stopping the containers.

- You should be able to access the web interface at `localhost:8000/admin`.
- To create a user for testing the web interface, run the below command and follow the prompts:
    - `docker exec -it web python src/manage.py createsuperuser`
- To setup initial configuration for the bots run:
    - `docker exec -it web python src/manage.py create_update_bot_accounts`
    - if the above command was run for the first time please make sure to run `docker exec -it web python src/manage.py migrate`. This will setup the celery tasks for the bots and their own loggers.
- To run the different modules individually, these commands should be run:
    - `docker exec -it web python src/manage.py pull_emails`
    - `docker exec -it web python src/manage.py push_emails`
    - `docker exec -it web python src/manage.py accept_invites`

#### For Testing Only
- Run the below command to add some initial data to the database for testing.
    - `docker exec -it web python src/manage.py seed_db_for_testing`