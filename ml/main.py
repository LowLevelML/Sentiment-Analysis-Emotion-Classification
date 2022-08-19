# -*- coding: utf-8 -*-
"""Sentiment-Analysis-Review-Classification.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1luZuFsWYGgwGDJBFQgrNKKL0RuY-Z7tH

# Import Data
"""

DATASETNAME = "emotion"

from datasets import load_dataset
dataset = load_dataset(DATASETNAME)

import torch
if torch.cuda.is_available():
	deviceName = "cuda"
else:
	deviceName = "cpu"
device = torch.device(deviceName)

"""# Preprocess Data"""

MODELNAME = "bert-base-uncased" # MODELNAME = "bert-large-uncased"

from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(MODELNAME)

def tokenize(batch):
    return tokenizer(batch["text"], padding=True, truncation=True)

datasetEncoded = dataset.map(tokenize, batched=True, batch_size=None)

datasetEncoded['train'][0]

from transformers import AutoModelForSequenceClassification

num_labels = 6
model = (AutoModelForSequenceClassification.from_pretrained(MODELNAME, num_labels=num_labels).to(device))

datasetEncoded["train"].features

datasetEncoded.set_format("torch", columns=["input_ids", "attention_mask", "label"])
datasetEncoded["train"].features

"""# Train the model"""

from sklearn.metrics import accuracy_score, f1_score

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    f1 = f1_score(labels, preds, average="weighted")
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc, "f1": f1}

from transformers import Trainer, TrainingArguments

batch_size = 64
logging_steps = len(datasetEncoded["train"]) // batch_size
training_args = TrainingArguments(output_dir="results",
                                  num_train_epochs=8,
                                  learning_rate=2e-5,
                                  per_device_train_batch_size=batch_size,
                                  per_device_eval_batch_size=batch_size,
                                  load_best_model_at_end=True,
                                  metric_for_best_model="f1",
                                  weight_decay=0.01,
                                  evaluation_strategy="epoch",
                                  save_strategy="epoch",
                                  disable_tqdm=False)

from transformers import Trainer

trainer = Trainer(model=model, args=training_args,
                  compute_metrics=compute_metrics,
                  train_dataset=datasetEncoded["train"],
                  eval_dataset=datasetEncoded["validation"])
trainer.train();

results = trainer.evaluate()
results

preds_output = trainer.predict(datasetEncoded["validation"])
preds_output.metrics

"""# Show results in a confusion matrix"""

import numpy as np
import seaborn as sns
from sklearn.metrics import plot_confusion_matrix
from sklearn.metrics import confusion_matrix
from sklearn.metrics import ConfusionMatrixDisplay
from matplotlib import pyplot as plt
def confusion_ma(y_true, y_pred, class_names):
    cm = confusion_matrix(y_true, y_pred, normalize='true')
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=class_names)
    disp.plot(cmap=plt.cm.Blues)
    return plt.show()
y_valid = np.array(datasetEncoded["validation"]["label"])
y_preds = np.argmax(preds_output.predictions, axis=1)
labels = ['sadness', 'joy', 'love', 'anger', 'fear', 'surprise']
# plot_confusion_matrix(y_preds, y_valid, labels)
# cm = confusion_matrix(y_preds, y_valid, labels, normalize=False)
# f = sns.heatmap(cm, annot=True)
confusion_ma(y_valid, y_preds, labels)