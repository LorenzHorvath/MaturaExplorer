import json


class QuestionManager:
    RELEVANT_DESCRIPTORS_FILE = "relevant_descriptors.json"
    DONE_QUESTIONS_FILE = "done_questions.json"
    MARKED_QUESTIONS_FILE = "marked_questions.json"
    QUESTIONS_FILE = "questions.json"

    def __init__(self):
        self.relevant_descriptors = self.read_json_file(self.RELEVANT_DESCRIPTORS_FILE)
        self.done_questions = self.read_questions(self.DONE_QUESTIONS_FILE)
        self.marked_questions = self.read_questions(self.MARKED_QUESTIONS_FILE)
        self.json_data = self.read_json_file(self.QUESTIONS_FILE)
        self.descriptor_count, self.descriptor_done_count, self.total_questions, self.done_questions_count = \
            self.calc_question_counts(self.json_data, self.done_questions, self.relevant_descriptors)
        self.descriptor_ratios = self.calculate_ratios(self.descriptor_count, self.descriptor_done_count)
        self.sorted_descriptors = []
        self.sort_descriptors()
        self.last_fetched_question_id = None

    @staticmethod
    def read_json_file(file_path):
        """Read JSON data from file."""
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"Error: File '{file_path}' not found.") from e
        except json.JSONDecodeError as e:
            raise ValueError(f"Error: Unable to decode JSON from file '{file_path}'.") from e

    @staticmethod
    def read_questions(filename):
        """Read questions from a file."""
        try:
            with open(filename, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            return []

    @staticmethod
    def write_questions(filename, questions):
        """Write questions to a file."""
        with open(filename, "w") as file:
            json.dump(questions, file)

    @staticmethod
    def calc_question_counts(data, done_questions, relevant_descriptors):
        """Calculate various counts related to questions and descriptors."""
        descriptor_count = {}
        descriptor_done_count = {}
        question_counter = 0
        unique_question_ids = set()
        done_question_counter = 0
        done_unique_question_ids = set()

        for question in data:
            question_id = question['id']
            descriptors = question['descriptors']

            relevant_descriptors_of_question = [descriptor for descriptor in descriptors if
                                                descriptor in relevant_descriptors]
            if relevant_descriptors_of_question or not relevant_descriptors:
                if question_id not in unique_question_ids:
                    question_counter += 1
                    unique_question_ids.add(question_id)
                    if question_id not in done_unique_question_ids and question_id in done_questions:
                        done_question_counter += 1
                        done_unique_question_ids.add(question_id)

                for descriptor in relevant_descriptors_of_question or descriptors:
                    if question_id in done_questions:
                        descriptor_done_count[descriptor] = descriptor_done_count.get(descriptor, 0) + 1
                    descriptor_count[descriptor] = descriptor_count.get(descriptor, 0) + 1

        return descriptor_count, descriptor_done_count, question_counter, done_question_counter

    @staticmethod
    def calculate_ratios(questions_per_descriptor, done_questions_per_descriptor):
        """Calculate completion ratios for each descriptor."""
        descriptor_ratios = {}

        for descriptor in questions_per_descriptor:
            total_questions_descriptor = questions_per_descriptor[descriptor]
            done_questions_descriptor = done_questions_per_descriptor.get(descriptor, 0)
            ratio_done = done_questions_descriptor / total_questions_descriptor \
                if total_questions_descriptor != 0 else 0
            descriptor_ratios[descriptor] = ratio_done

        return descriptor_ratios

    def sort_descriptors(self):
        """Sort descriptors based on completion ratios."""
        sorted_descriptors = sorted(
            [descriptor for descriptor in self.descriptor_ratios.keys() if descriptor.startswith(
                ("B_T_", "B_T2", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))],
            key=lambda x: (self.descriptor_ratios[x],) + tuple(
                map(lambda y: int(y) if y.isdigit() else y, x.split('_'))),
            reverse=False
        )

        self.sorted_descriptors = sorted_descriptors

    def show_stats(self):
        """Display statistics about questions and descriptors."""
        if not self.descriptor_count:
            print("No relevant descriptors found.")
            return

        total_ratio_done = self.done_questions_count / self.total_questions if self.total_questions else 0

        print(f"Total Questions: {self.total_questions}")
        print(f"Percent of questions done: {total_ratio_done * 100:.2f}%\n")

        print(f"Descriptor".ljust(10), "Total".rjust(9), "Percent Done".rjust(15))
        print("-" * 36)

        for descriptor in self.sorted_descriptors:
            total_descriptor = self.descriptor_count.get(descriptor, 0)
            ratio = self.descriptor_ratios.get(descriptor, 0)
            print(f"{descriptor.ljust(10)}{str(total_descriptor).rjust(10)}", f"{ratio * 100:.2f}%".rjust(15))

        print()

    @staticmethod
    def print_help():
        """Display list of available commands."""
        print("\nCommand        Description\n"
              "------------------------------------------------------------------------------------------------------\n"
              "get            Get a question of the descriptor sorted on top.\n"
              "done [ID]      Declare a question as done. If no ID provided, the last fetched question will be saved.\n"
              "mark [ID]      Mark a question. If no ID provided, the last fetched question will be saved.\n"
              "stats          Get statistics.\n"
              "help           Display list of commands.\n"
              "quit           Quit and save your changes.\n")

    def main(self):
        """Main method to handle user interactions."""
        self.print_help()

        print("To filter by specific descriptors, use the 'relevant_descriptors.json' file.")
        print("Make sure to exit using the 'quit' command to save your changes.")

        while True:
            user_input = input()
            if user_input.lower() == 'get':
                top_descriptor = self.sorted_descriptors[0]
                found_question = False
                for question in self.json_data:
                    if (top_descriptor in question['descriptors'] and
                            question['id'] not in self.done_questions and
                            question['id'] not in self.marked_questions):
                        self.last_fetched_question_id = question['id']
                        print(f"Question: {question['title']}, "
                              f"Question ID: {question['id']}, "
                              f"Descriptor: {top_descriptor}, "
                              f"Link: {question['beamer_link']}")
                        found_question = True
                        break
                if not found_question:
                    print("No available question for the top descriptor.")
            elif user_input.lower().startswith('done'):
                if len(user_input.split()) == 1 and self.last_fetched_question_id:
                    self.done_questions.append(self.last_fetched_question_id)
                else:
                    self.done_questions.append(user_input[5:])
                self.descriptor_count, self.descriptor_done_count, self.total_questions, self.done_questions_count \
                    = self.calc_question_counts(self.json_data, self.done_questions, self.relevant_descriptors)
                self.descriptor_ratios = self.calculate_ratios(self.descriptor_count, self.descriptor_done_count)
                self.sort_descriptors()
                print("Questions successfully declared as done.")
            elif user_input.lower().startswith('mark'):
                if len(user_input.split()) == 1 and self.last_fetched_question_id:
                    self.marked_questions.append(self.last_fetched_question_id)
                else:
                    self.marked_questions.append(user_input[5:])
                print("Question successfully marked.")
            elif user_input.lower() == 'stats':
                self.show_stats()
            elif user_input.lower() == 'help':
                self.print_help()
            elif user_input.lower() == 'quit':
                self.write_questions(self.DONE_QUESTIONS_FILE, self.done_questions)
                self.write_questions(self.MARKED_QUESTIONS_FILE, self.marked_questions)
                break


if __name__ == "__main__":
    question_manager = QuestionManager()
    question_manager.main()
