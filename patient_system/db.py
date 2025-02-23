import sqlite3
import json


class PatientDatabase:
    def __init__(self, db_name="patient_data.db"):
        """
        Initializes the PatientDatabase class and connects to the SQLite database.

        Args:
            db_name (str, optional): The name of the database file.
                Defaults to "patient_data.db".
        """
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        """
        Creates the necessary tables in the database if they don't exist.
        """
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                address TEXT,
                identity TEXT,
                phone TEXT,
                description TEXT,
                recommended_doctor TEXT
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS problems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                name TEXT,
                duration TEXT,
                description TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS conditions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER,
                condition TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """
        )
        self.conn.commit()

    def create_patient(self, patient_data):
        """
        Creates a new patient record in the database.

        Args:
            patient_data (dict): A dictionary containing patient information.
        """
        try:
            # Insert patient data into the patients table
            self.cursor.execute(
                """
                INSERT INTO patients (name, age, gender, address, identity,
                phone, description, recommended_doctor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    patient_data["name"],
                    patient_data["age"],
                    patient_data["gender"],
                    patient_data["address"],
                    patient_data["identity"],
                    patient_data["phone"],
                    patient_data["description"],
                    patient_data["recommended_doctor"],
                ),
            )
            patient_id = self.cursor.lastrowid  # Get the ID of the newly inserted patient

            # Insert problems into the problems table
            for problem in patient_data.get("problems", []):
                self.cursor.execute(
                    """
                    INSERT INTO problems (patient_id, name, duration, description)
                    VALUES (?, ?, ?, ?)
                """,
                    (patient_id, problem["name"], problem["duration"], problem["description"]),
                )

            # Insert conditions into the conditions table
            for condition in patient_data.get("conditions", []):
                self.cursor.execute(
                    """
                    INSERT INTO conditions (patient_id, condition)
                    VALUES (?, ?)
                """,
                    (patient_id, condition),
                )

            self.conn.commit()
            return patient_id
        except Exception as e:
            self.conn.rollback()
            print(f"Error creating patient: {e}")
            return None

    def select_patient(self, patient_id):
        """
        Retrieves a patient record from the database by ID.

        Args:
            patient_id (int): The ID of the patient to retrieve.

        Returns:
            dict: A dictionary containing the patient's information, or None if
                the patient is not found.
        """
        try:
            # Select patient data from the patients table
            self.cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
            patient_row = self.cursor.fetchone()

            if patient_row:
                patient_data = {
                    "id": patient_row[0],
                    "name": patient_row[1],
                    "age": patient_row[2],
                    "gender": patient_row[3],
                    "address": patient_row[4],
                    "identity": patient_row[5],
                    "phone": patient_row[6],
                    "description": patient_row[7],
                    "recommended_doctor": patient_row[8],
                    "problems": [],
                    "conditions": [],
                }

                # Select problems from the problems table
                self.cursor.execute(
                    "SELECT name, duration, description FROM problems WHERE patient_id = ?",
                    (patient_id,),
                )
                problem_rows = self.cursor.fetchall()
                for row in problem_rows:
                    patient_data["problems"].append(
                        {"name": row[0], "duration": row[1], "description": row[2]}
                    )

                # Select conditions from the conditions table
                self.cursor.execute(
                    "SELECT condition FROM conditions WHERE patient_id = ?", (patient_id,)
                )
                condition_rows = self.cursor.fetchall()
                patient_data["conditions"] = [row[0] for row in condition_rows]

                return patient_data
            else:
                return None
        except Exception as e:
            print(f"Error selecting patient: {e}")
            return None

    def select_all_patients(self):
        """
        Retrieves all patient records from the database.

        Returns:
            list: A list of dictionaries, where each dictionary represents a
                patient's information.  Returns an empty list if no patients
                are found.
        """
        try:
            self.cursor.execute("SELECT id FROM patients")  # Just get the IDs
            patient_ids = [row[0] for row in self.cursor.fetchall()]  # Extract IDs

            all_patients = []
            for patient_id in patient_ids:
                patient_data = self.select_patient(patient_id)  # Use existing function
                if patient_data:  # Only add if select_patient returned something
                    all_patients.append(patient_data)

            return all_patients
        except Exception as e:
            print(f"Error selecting all patients: {e}")
            return []

    def delete_patient(self, patient_id):
        """
        Deletes a patient record from the database.

        Args:
            patient_id (int): The ID of the patient to delete.
        """
        try:
            # Delete problems associated with the patient
            self.cursor.execute("DELETE FROM problems WHERE patient_id = ?", (patient_id,))

            # Delete conditions associated with the patient
            self.cursor.execute("DELETE FROM conditions WHERE patient_id = ?", (patient_id,))

            # Delete the patient from the patients table
            self.cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))

            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            print(f"Error deleting patient: {e}")
            return False

    def close(self):
        """
        Closes the database connection.
        """
        self.conn.close()

def print_schema(db_name="patient_data.db"):
    """
    Prints the schema of a SQLite database.

    Args:
        db_name (str, optional): The name of the database file.
            Defaults to "patient_data.db".
    """
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [row[0] for row in cursor.fetchall()]

        for table_name in table_names:
            print(f"Schema for table: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            for column in columns:
                cid, name, type, notnull, dflt_value, pk = column
                print(
                    f"  Column: {name}, Type: {type}, Not Null: {notnull}, "
                    f"Default Value: {dflt_value}, Primary Key: {pk}"
                )
            print("-" * 30)

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()