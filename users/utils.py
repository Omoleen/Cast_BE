from abc import ABC

import pandas as pd


class UserFileImport(ABC):
    def __init__(self, file, valid_columns=None):
        if valid_columns is None:
            valid_columns = ["first_name", "last_name", "email"]
        self.variable_columns = ["department"]
        self.file = file
        self.valid_columns = valid_columns
        self.columns = None
        self.df = None
        self.missing_columns = []
        self.errors = []

    def generate_df(self):
        file = self.file
        if file.name.endswith(".csv"):
            df: pd.DataFrame = pd.read_csv(file)
            self.df = df
        elif file.name.endswith(".xlsx"):
            df: pd.DataFrame = pd.read_excel(file)
            self.df = df

    def handle_file(self):
        valid_columns = self.valid_columns
        df = self.df
        original_columns: list[str] = df.columns

        columns: list = [
            column.strip().replace(" ", "_").lower() for column in original_columns
        ]

        df.rename(
            columns={
                original_columns[i]: columns[i] for i in range(len(original_columns))
            },
            inplace=True,
        )

        columns = df.columns

        missing_columns = [column for column in valid_columns if not column in columns]

        self.columns = columns
        self.df = df
        self.missing_columns = missing_columns

    def is_valid(self):
        self.generate_df()
        self.handle_file()
        missing_columns = self.missing_columns

        if missing_columns:
            self.errors = []
            for column in missing_columns:
                self.errors.append(
                    {
                        "row": 1,
                        "column": column,
                        "message": f"Column {column} is missing",
                    }
                )
            return False

        return True

    def get_records(self):
        df = self.df
        records = df.to_dict("records")
        return records

    @property
    def records(self):
        return self.get_records()


class UserCSVImport(UserFileImport):
    def generate_df(self):
        file = self.file
        df: pd.DataFrame = pd.read_csv(file)

        self.df = df


class UserXLSXImport(UserFileImport):
    def generate_df(self):
        file = self.file
        df: pd.DataFrame = pd.read_excel(file)

        self.df = df
