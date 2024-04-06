import json


def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except json.JSONDecodeError:
        print(f"Error: Unable to decode JSON from file '{file_path}'.")

    return None


RELEVANT_DESCRIPTORS = read_json_file("relevant_descriptors.json")


def read_questions(filename):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def write_questions(filename, questions):
    with open(filename, "w") as file:
        json.dump(questions, file)


def calc_question_counts(data, done_questions):
    descriptor_count = {}
    done_questions_count = {}

    for question in data:
        question_id = question['id']
        descriptors = question['descriptors']
        for descriptor in descriptors:
            if RELEVANT_DESCRIPTORS and descriptor not in RELEVANT_DESCRIPTORS:
                continue
            if question_id in done_questions:
                done_questions_count[descriptor] = done_questions_count.get(descriptor, 0) + 1
            descriptor_count[descriptor] = descriptor_count.get(descriptor, 0) + 1

    return descriptor_count, done_questions_count


def calculate_ratios(descriptor_count, done_questions_count):
    descriptor_ratios = {}

    for descriptor in descriptor_count:
        total_questions_descriptor = descriptor_count[descriptor]
        done_questions_descriptor = done_questions_count.get(descriptor, 0)
        ratio_done = done_questions_descriptor / total_questions_descriptor if total_questions_descriptor != 0 else 0
        descriptor_ratios[descriptor] = ratio_done

    return descriptor_ratios


def show_stats(descriptor_count, descriptor_ratios):
    if not sorted_descriptors:
        print("No relevant descriptors found.")
        return

    total_questions = sum(descriptor_count.values())
    total_done = sum(descriptor_count[descriptor] * ratio for descriptor, ratio in descriptor_ratios.items())
    total_ratio_done = total_done / total_questions if total_questions else 0

    print(f"Total Questions: {total_questions}")
    print(f"Percent of questions done: {total_ratio_done * 100:.2f}%\n")

    print(f"Descriptor".ljust(10), "Total".rjust(9), "Percent Done".rjust(15))
    print("-" * 36)

    for descriptor in sorted_descriptors:
        total_descriptor = descriptor_count.get(descriptor, 0)
        ratio = descriptor_ratios.get(descriptor, 0)
        print(f"{descriptor.ljust(10)}{str(total_descriptor).rjust(10)}", f"{ratio * 100:.2f}%".rjust(15))


def print_help():
    print("\nCommand         Description\n"
          "-------------------------------------------------------------------------------------------------------\n"
          "get             Get a question of the descriptor sorted on top.\n"
          "done [ID]       Declare a question as done. If no ID provided, the last fetched question will be saved.\n"
          "mark [ID]       Mark a question. If no ID provided, the last fetched question will be saved.\n"
          "stats           Get statistics.\n"
          "help            Display list of commands.\n"
          "quit            Quit and save your changes.\n")


def sort_descriptors(descriptor_ratios):
    global sorted_descriptors
    sorted_descriptors = sorted(
        [descriptor for descriptor in descriptor_ratios.keys() if descriptor.startswith(
            ("B_T_", "B_T2", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"))],
        key=lambda x: (descriptor_ratios[x],) + tuple(map(lambda y: int(y) if y.isdigit() else y, x.split('_'))),
        reverse=False
    )


def main():
    file_path = "questions.json"
    done_questions = read_questions("done_questions.json")
    marked_questions = read_questions("marked_questions.json")
    json_data = read_json_file(file_path)

    last_fetched_question_id = None

    descriptor_count, done_questions_count = calc_question_counts(json_data, done_questions)
    descriptor_ratios = calculate_ratios(descriptor_count, done_questions_count)

    sort_descriptors(descriptor_ratios)

    show_stats(descriptor_count, descriptor_ratios)

    print_help()

    print("To filter by specific descriptors, use the 'relevant_descriptors.json' file.")
    print("Make sure to exit using the 'quit' command to save your changes.")

    while True:
        user_input = input()
        if user_input.lower() == 'get':
            top_descriptor = sorted_descriptors[0]
            found_question = False
            for question in json_data:
                if (top_descriptor in question['descriptors'] and
                        question['id'] not in done_questions and
                        question['id'] not in marked_questions):
                    last_fetched_question_id = question['id']
                    print(f"Question: {question['title']}, "
                          f"Question ID: {question['id']}, "
                          f"Descriptor: {top_descriptor}, "
                          f"Link: {question['beamer_link']}")
                    found_question = True
                    break
            if not found_question:
                print("No available question for the top descriptor.")
        elif user_input.lower().startswith('done'):
            if len(user_input.split()) == 1 and last_fetched_question_id:
                done_questions.append(last_fetched_question_id)
            else:
                done_questions.append(user_input[5:])
            descriptor_count, done_questions_count = calc_question_counts(json_data, done_questions)
            descriptor_ratios = calculate_ratios(descriptor_count, done_questions_count)
            sort_descriptors(descriptor_ratios)
            print("Questions successfully declared as done.")
        elif user_input.lower().startswith('mark'):
            if len(user_input.split()) == 1 and last_fetched_question_id:
                marked_questions.append(last_fetched_question_id)
            else:
                marked_questions.append(user_input[5:])
            print("Question successfully marked.")
        elif user_input.lower() == 'stats':
            show_stats(descriptor_count, descriptor_ratios)
        elif user_input.lower() == 'help':
            print_help()
        elif user_input.lower() == 'quit':
            write_questions("done_questions.json", done_questions)
            write_questions("marked_questions.json", marked_questions)
            break


global sorted_descriptors

if __name__ == "__main__":
    main()
