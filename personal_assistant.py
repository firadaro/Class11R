import json
import re
import pandas as pd
import os
from datetime import datetime

class BaseStorage:

    def load_storage(self):
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r") as f:
                loaded_data = json.load(f)
                return {int(k): v for k, v in loaded_data.items()}
        return {}

    def __init__(self, params, storage_path, short_title):
        self.params = params
        self.storage_path = storage_path
        self.data = self.load_storage()
        self.short_title = short_title

        self.date_validator = re.compile(r'^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-(\d{4})$')
        self.datetime_validator = re.compile(r'^(0[1-9]|[12][0-9]|3[01])-(0[1-9]|1[0-2])-(\d{4})\s([01][0-9]|2[0-3]):([0-5][0-9]):([0-5][0-9])$')
        self.max_id = 0 if len(self.data) == 0 else max(self.data.keys()) + 1

        self.num_to_id = {i: x["id"] for i, x in enumerate(self.data.values())}

    def validate(self, param, value):
        if self.params[param] == "date":
            return bool(self.date_validator.match(value))
        if self.params[param] == "datetime":
            return bool(self.datetime_validator.match(value))
        if self.params[param] == "bool":
            return value in ["True", "False", ""]
        try:
            eval(self.params[param])(value)
            return True
        except:
            return False

    def save_storage(self):
        with open(self.storage_path, "w") as f:
            json.dump(self.data, f)

    def add_sample(self, sample):
        print(sample, self.max_id)
        sample["id"] = self.max_id
        self.data[self.max_id] = sample
        self.num_to_id[len(self.data)] = self.max_id
        self.max_id += 1

    def create(self, update_index=None):
        new_data = {}
        for param in self.params:
            if param == "id":
                continue
            if param == "timestamp":
                now = datetime.now()
                formatted_time = now.strftime("%d-%m-%Y %H:%M:%S")
                new_data[param] = formatted_time
                continue
            while True:
                value = input(f"Введите {param}:")
                if self.validate(param, value):
                    new_data[param] = value
                    break
                else:
                    print("Некорректное значение")
        if update_index is not None:
            self.data[self.num_to_id[update_index]] = new_data
        else:
            self.add_sample(new_data)
        self.save_storage()
        return update_index if update_index is not None else len(self.data)

    def remove(self, index, is_id=False):
        if not is_id:
            index_ = self.num_to_id[index]
        del self.data[index_]
        new_num_to_id = self.num_to_id.copy()
        for k, v in self.num_to_id.items():
            if k > self.num_to_id[index_]:
                new_num_to_id[k - 1] = self.num_to_id[k]
        del new_num_to_id[len(new_num_to_id) - 1]
        self.num_to_id = new_num_to_id
        self.save_storage()

    def update(self, index, is_id=False):
        if not is_id:
            index = self.num_to_id[index]
        self.create(update_index=self.num_to_id[index])

    def read(self, index):
        for key, value in self.data[self.num_to_id[index]].items():
            if key != "id":
                print(f"{key}: {value}", end=", ")
        print("\n")

    def read_all(self):
        for i, x in enumerate(self.data):
            print(f"{i}: {self.data[x][self.short_title]}\n")

    def save_as_csv(self):
        path = input("Введите путь до экспорта: ")
        pd.DataFrame([self.data[k] for k in self.data.keys()]).to_csv(path, index=False)

    def load_from_csv(self):
        path = input("Введите путь для импорта")
        df = pd.read_csv(path, index_col=False)

        for _, row in df.iterrows():
            flag = True
            new_data = {}
            for col in df.columns:
                if not (col in self.params and self.validate(col, row[col])):
                    flag = False
                    break
                new_data[col] = row[col]
            if flag:
                self.add_sample(new_data)

class TasksStorage(BaseStorage):

    def create_task(self, update_index=None):
        new_id = self.num_to_id[self.create(update_index)]
        if self.data[new_id]["done"] == "":
            self.data[new_id]["done"] = "False"
            self.save_storage()

    def mark_completed(self, index):
        self.data[self.num_to_id[index]]["done"] = "True"

    def read_all(self):
        for i, data in self.data.items():
            print(i, end='. ')
            for key, value in data.items():
                if key != "id":
                    print(f"{key}: {value}", end=", ")
            print('\n')

class ContactsStorage(BaseStorage):

    def search_by_param(self, param, value, return_id=False):
        for k, v in self.data.items():
            if v[param] == value:
                if return_id:
                    return v["id"]
                for param_name, param_value in v.items():
                    if param_name != "id":
                        print(f"{param_name}: {param_value}", end=", ")
                print("\n")

    def search_by_phone(self, phone):
        self.search_by_param("phone", phone)

    def search_by_name(self, name):
        self.search_by_param("name", name)

    def edit_contact(self, name):
        id_ = self.search_by_param("name", name, True)
        self.update(id_, is_id=True)

    def remove_contact(self, name):
        id_ = self.search_by_param("name", name, True)
        self.remove(id_, is_id=True)

class FinancialStorage(BaseStorage):

    def print_all_by_param(self, param=None, value=None):
        i = 1
        for k, v in self.data.items():
            if param is None or v[param] == value:
                for p, v_ in v.items():
                    print(f"{i}. {p}: {v[p]}", end=", ")
                print("\n")
                i += 1

    def generate_report(self, date1, date2):
        to_date = lambda x: datetime.strptime(x, "%d-%m-%Y").date()
        date1 = to_date(date1)
        date2 = to_date(date2)

        income = 0
        outcome = 0
        for k, v in self.data.items():
            if to_date(v["date"]) <= date2 and date1 <= to_date(v["date"]):
                amount = float(v["amount"])
                if amount > 0:
                    income += amount
                else:
                    outcome += amount
        print(f"Отчет за {date1} - {date2}")
        print(f"Общий доход: {income}")
        print(f"Общий расход: {outcome}")
        print(f"Баланс: {income + outcome}")

class App:

    def __init__(self):

        with open("./dialogs.json", "r") as f:
            self.dialogues = json.load(f)
        self.not_jsoned_names = ["calculator", "exit"]
        self.notes_storage = BaseStorage({"id": "int",
                                          "title": "str",
                                          "content": "str",
                                          "timestamp": "datetime"},
                                         "notes.json",
                                         "title")

        self.tasks_storage = TasksStorage({"id": "int",
                                           "title": "str",
                                           "description": "str",
                                           "done": "bool",
                                           "priority": "str",
                                           "due_date": "date"},
                                          "tasks.json",
                                          "title")

        self.contacts_storage = ContactsStorage({"id": "int",
                                                 "name": "str",
                                                 "phone": "str",
                                                 "email": "str"},
                                                "contacts.json",
                                                "name")

        self.finance_storage = FinancialStorage({"id": "int",
                                               "amount": "float",
                                               "category": "str",
                                               "date": "date",
                                               "description": "str"},
                                              "finance.json",
                                              "amount")

    def safe_eval(self, expression):
        if not re.match(r'^[\d\s()+\-*/.]+$', expression):
            return "Некорректное арифметическое выражение."
            
        try:
            result = eval(expression)
            return result
        except Exception as e:
            return "Ошибка при вычислении выражения."

    def calculator_(self):
        expression = input("Введите выражение для вычисления: ")
        print(self.safe_eval(expression))
                                          

    def stringify_choices_(self, choices):
        result_string = ""
        for key, value in choices.items():
            result_string += value["text"]
        return result_string

    def create_note_(self):
        self.notes_storage.create()

    def view_notes_list_(self):
        self.notes_storage.read_all()

    def view_note_details_(self):
        index = int(input("Введите номер заметки: "))
        self.notes_storage.read(index)

    def edit_note_(self):
        index = int(input("Введите номер заметки: "))
        self.notes_storage.update(index)

    def delete_note_(self):
        index = int(input("Введите номер заметки: "))
        self.notes_storage.remove(index)

    def import_notes_csv_(self):
        self.notes_storage.load_from_csv()

    def export_notes_csv_(self):
        self.notes_storage.save_as_csv()

    def stringify_json_(self, json_data):
        result_string = ""
        for x in json_data:
            for key, value in x.items():
                result_string += f"{key}: {value}"
            result_string += "\n"
        return result_string

    def read_json_(self, json_name):
        with open(f"{json_name}.json", "r") as f:
            jsoned_data = json.load(f)
        return jsoned_data

    def save_json(self, json_name, json_data):
        with open(f"{json_name}.json", "r") as f:
            json.dump(json_data, f)

    def handle_base_choice(self, choice_name):
        print(self.stringify_choices_(self.dialogues[choice_name]))
        user_answer = input("Выберите действие: ")
        getattr(self, self.dialogues[choice_name][user_answer]["func"])()

    def exit_(self):
        exit()

    def notes_menu_(self):
        self.handle_base_choice("notes")

    def tasks_menu_(self):
        self.handle_base_choice("tasks")

    def create_task_(self):
        self.tasks_storage.create_task()

    def view_tasks_list_(self):
        self.tasks_storage.read_all()

    def mark_task_completed_(self):
        index = int(input("Введите номер задачи для отметки как выполненной: "))
        self.tasks_storage.mark_completed(index)

    def edit_task_(self):
        index = int(input("Введите номер задачи для редактирования: "))
        self.tasks_storage.update(index)

    def delete_task_(self):
        index = int(input("Введите номер задачи для удаления: "))
        self.tasks_storage.remove(index)

    def import_tasks_csv_(self):
        self.tasks_storage.load_from_csv()

    def export_tasks_csv_(self):
        self.tasks_storage.save_as_csv()

    def contacts_menu_(self):
        self.handle_base_choice("contacts")

    def add_contact_(self):
        self.contacts_storage.create()

    def search_contact_by_name_(self):
        name = input("Введите имя для поиска: ")
        self.contacts_storage.search_by_name(name)

    def search_contact_by_phone_(self):
        name = input("Введите номер для поиска: ")
        self.contacts_storage.search_by_name(name)

    def edit_contact_(self):
        name = int(input("Введите имя контакта для редактирования: "))
        self.contacts_storage.edit_contact(name)

    def remove_contact_(self):
        name = int(input("Введите имя контакта для удаления: "))
        self.contacts_storage.remove_contact(name)

    def import_contacts_(self):
        self.contacts_storage.load_from_csv()

    def export_contacts_(self):
        self.contacts_storage.save_as_csv()

    def fin_menu_(self):
        self.handle_base_choice("finance")

    def add_financial_record_(self):
        self.finance_storage.create()

    def view_financial_records_(self):
        self.finance_storage.print_all_by_param(None, None)

    def view_financial_records_categ_(self):
        category = input("Введите категорию: ")
        self.finance_storage.print_all_by_param("category", category)

    def view_financial_records_date_(self):
        date = input("Введите дату: ")
        self.finance_storage.print_all_by_param("date", date)

    def generate_financial_report_(self):
        date1 = input("Введите начало периода: ")
        date2 = input("Введите конец периода: ")
        self.finance_storage.generate_report(date1, date2)

    def import_financial_records_csv_(self):
        self.finance_storage.load_from_csv()

    def export_financial_records_csv_(self):
        self.finance_storage.save_as_csv()
    
    def run(self):
        while True:
            self.handle_base_choice("menu")

if __name__ == "__main__":
    app = App()
    app.run()