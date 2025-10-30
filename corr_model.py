from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
import torch
from sklearn.model_selection import train_test_split
from torch.utils.data import Dataset


# Данные: предложения и их метки
texts = [
    "Привет, как твои дела?",   # Ничего не значащее
    "Проект готов к запуску.",  # Значимое
    "Что нового?",              # Ничего не значащее
    "Давайте обсудим план проекта.",  # Значимое
    "Привет",
    "привет",
    "ПРИВЕТ",
    "Пока",
    "ПОКА",
    "пока",
    "как дела",
    "Ну что, дружище",
    "Дружище",
    "как ты?",
    "Как ты?",
    "В просторечии под экологией часто понимается состояние окружающей среды, а под экологическими проблемами — вопросы охраны окружающей среды от воздействия антропогенных факторов",
    "Экологизм — общественное движение за усиление мер охраны окружающей среды и за предотвращение разрушения среды обитания.",
    "Британская энциклопедия рассматривает в качестве первых истоков экологии как науки работы древнегреческих естествоиспытателей, в первую очередь Теофраста, описывавшего отношения организмов между собой и с окружающей неживой природой. Дальнейшее развитие этой области науки дали ранние исследователи физиологии растений и животных",

]
labels = [0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1]  # Метки для всех текстов

# Токенизация
tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=128)

# Разделение данных
input_ids_train, input_ids_test, labels_train, labels_test = train_test_split(
    inputs["input_ids"],
    labels,
    test_size=0.2,
    random_state=42
)
attention_mask_train, attention_mask_test = train_test_split(
    inputs["attention_mask"],
    test_size=0.2,
    random_state=42
)

# Подготовка словарей для датасета
train_encodings = {"input_ids": input_ids_train, "attention_mask": attention_mask_train}
test_encodings = {"input_ids": input_ids_test, "attention_mask": attention_mask_test}

# Кастомный класс для датасета
class CustomDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx])
        return item

# Создаем тренировочный и тестовый датасеты
train_dataset = CustomDataset(train_encodings, labels_train)
test_dataset = CustomDataset(test_encodings, labels_test)

# Модель
model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)

# Настройка обучения
training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",
    per_device_train_batch_size=8,
    num_train_epochs=3,
    logging_dir="./logs",
    save_strategy="epoch",
    load_best_model_at_end=True
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

# Обучение
trainer.train()

# Функция классификации
def classify_texts(model, tokenizer, texts):
    """
    Классификация списка текстов.
    """
    # Токенизация новых текстов
    inputs = tokenizer(texts, padding=True, truncation=True, return_tensors="pt", max_length=128)

    # Инференс
    with torch.no_grad():
        outputs = model(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"])
        predictions = torch.argmax(outputs.logits, dim=-1).numpy()

    return predictions

# Пример применения
new_texts = [
    "Как дела?",  # Ничего не значащее
    "Пора начинать проект.",  # Значимое
    "В просторечии под экологией часто понимается состояние окружающей среды, а под экологическими проблемами — вопросы охраны окружающей среды от воздействия антропогенных факторов"
]
predictions = classify_texts(model, tokenizer, new_texts)
print(predictions)  # Ожидаемый результат: [0, 1]



# def filter_fragments(model, tokenizer, text):
#     """
#     Удаляет ничего не значащие предложения из текста.
#     :param model: Обученная модель BERT.
#     :param tokenizer: Токенайзер.
#     :param text: Входной текст (строка).
#     :return: Очищенный текст.
#     """
#     # Разбиваем текст на предложения
#     from nltk.tokenize import sent_tokenize
#     sentences = sent_tokenize(text)
#
#     # Токенизация предложений
#     inputs = tokenizer(sentences, padding=True, truncation=True, return_tensors="pt", max_length=128)
#
#     # Предсказания модели
#     with torch.no_grad():
#         outputs = model(**inputs)
#         predictions = torch.argmax(outputs.logits, dim=-1).numpy()
#
#     # Фильтруем только значимые предложения
#     filtered_sentences = [sentence for sentence, label in zip(sentences, predictions) if label == 1]
#     return " ".join(filtered_sentences)
#
# # Пример использования
# text = "Привет, как твои дела? Проект готов к запуску. Что нового? Давайте обсудим план проекта."
# cleaned_text = filter_fragments(model, tokenizer, text)
# print(cleaned_text)  # "Проект готов к запуску. Давайте обсудим план проекта."