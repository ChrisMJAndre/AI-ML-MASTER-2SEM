# -*- coding: utf-8 -*-
"""
Created on Sun Apr 30 14:24:59 2023

@author: chris
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
import seaborn as sns
import matplotlib.pyplot as plt
from collections import Counter
from nltk.util import ngrams
from nltk.tokenize import word_tokenize


# Read dataset
dataset1 = pd.read_pickle("data_seperated_gbt1.pkl")
dataset2 = pd.read_pickle("data_seperated_gbt2.pkl")
dataset3 = pd.read_pickle("data_seperated_gbt3.pkl")
dataset4 = pd.read_pickle("data_seperated_gbt4.pkl")
dataset5 = pd.read_pickle("data_seperated_gbt5.pkl")
dataset6 = pd.read_pickle("data_seperated_gbt6.pkl")
dataset7 = pd.read_pickle("data_seperated_gbt7.pkl")
dataset8 = pd.read_pickle("data_seperated_gbt8.pkl")
dataset9 = pd.read_pickle("data_seperated_gbt9.pkl")
dataset10 = pd.read_pickle("data_seperated_gbt10.pkl")

# Merge dataset
DatasetBig = pd.concat([dataset1, dataset2, dataset3, dataset4, dataset5, dataset6, dataset7, dataset8, dataset9, dataset10],ignore_index=True)


#Drop date for now - perhaps in the real one, loot out all the ones after 2022? 
dataset = DatasetBig.drop(['update_date',], axis=1)

# Create a binary label for AI text (1) and human text (0)
dataset["is_ai_generated"] = dataset["ai_generated"].apply(lambda x: 1 if x else 0)


removed1 = dataset[dataset['abstract'].str.contains('Unfortunately',regex=False) & dataset["ai_generated"] == 1]
dataset = dataset.drop(removed1.index)

removed2 = dataset[dataset['abstract'].str.len() < 500]
dataset = dataset.drop(removed2.index)

new_dataset = pd.read_csv('AI & ML texts.csv', sep=';')
new_dataset["is_ai_generated"] = new_dataset["ai_generated"].apply(lambda x: 1 if x else 0)



#------------------------------------------ Perplexity ----------------------------------------------------#


#https://huggingface.co/docs/transformers/perplexity 
def calculate_perplexity_gpt2(text, tokenizer, model):
    tokens = tokenizer.encode(text, return_tensors="pt")
    
    with torch.no_grad(): #Makes it process faster and with less memory  (does not track gradients)
        outputs = model(tokens, labels=tokens)
        loss = outputs.loss #Returns the loss function, (a measure of how well it predicted the text)
        perplexity = torch.exp(loss).item() 
    return perplexity


def add_perplexity_column_huggingface(df):
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2").eval()

    perplexities = [calculate_perplexity_gpt2(text, tokenizer, model) for text in df["abstract"]]
    df["Perplexity"] = perplexities

    return df

def add_perplexity_column_huggingface_1(df):
    print("Loading models")
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    model = GPT2LMHeadModel.from_pretrained("gpt2").eval()
    print("Finished Loading models")
    perplexities = []
    for i, text in enumerate(df["abstract"]):
        perplexity = calculate_perplexity_gpt2(text, tokenizer, model)
        perplexities.append(perplexity)
        print(f"Finished processing text {i+1}/{len(df)}")

    df["Perplexity"] = perplexities

    return df

dataset_with_perplexity = add_perplexity_column_huggingface_1(dataset)

new_dataset = add_perplexity_column_huggingface_1(new_dataset)

print(dataset_with_perplexity.head())



# Create a box plot to visualize the distribution of perplexity scores
plt.figure(figsize=(10, 6))
ax = sns.boxplot(x="is_ai_generated", y="Perplexity", data=dataset_with_perplexity,showfliers = False) ##REMOVED OUTLIERS!! 
#ax = sns.boxplot(x="is_ai_generated", y="Perplexity", data=dataset_with_perplexity) 
ax.set_xticklabels(["Human-generated", "AI-generated"])
ax.set_xlabel("Text")
ax.set_ylabel("Perplexity")
ax.set_title("Perplexity Distribution for Human-generated vs. AI-generated Text")

plt.show()

# Create a box plot to visualize the distribution of perplexity scores
plt.figure(figsize=(10, 6))
ax = sns.boxplot(x="is_ai_generated", y="Perplexity", data=new_dataset,showfliers = False) ##REMOVED OUTLIERS!! 
#ax = sns.boxplot(x="is_ai_generated", y="Perplexity", data=dataset_with_perplexity) 
ax.set_xticklabels(["Human-generated", "AI-generated"])
ax.set_xlabel("Text")
ax.set_ylabel("Perplexity")
ax.set_title("Perplexity Distribution for Human-generated vs. AI-generated Text")

plt.show()

#---------------------------------- Statistics -------------------------------------------#

def ngram_distribution(texts, max_ngram_length):
    all_ngrams = []
    for text in texts:
        tokens = word_tokenize(text)
        for n in range(1, max_ngram_length + 1):
            text_ngrams = list(ngrams(tokens, n))
            all_ngrams.extend(text_ngrams)
    return Counter(all_ngrams)

def descriptive_statistics(df, max_ngram_length=8):
    human_texts = df[df["is_ai_generated"] == 0]["abstract"]
    ai_texts = df[df["is_ai_generated"] == 1]["abstract"]
    
    return {
        "Human N-gram Distribution": ngram_distribution(human_texts, max_ngram_length),
        "AI N-gram Distribution": ngram_distribution(ai_texts, max_ngram_length),
        "Human Average Text Length": np.mean([len(word_tokenize(text)) for text in human_texts]),
        "AI Average Text Length": np.mean([len(word_tokenize(text)) for text in ai_texts]),
        "Human Average Text character Length": np.mean([len([*text]) for text in human_texts]),
        "AI Average Text character Length": np.mean([len([*text]) for text in ai_texts]),
        
        "Human Average Text character Length pr word": np.mean([len([*text]) for text in human_texts])/np.mean([len(word_tokenize(text)) for text in human_texts]),
        "AI Average Text character Length pr word": np.mean([len([*text]) for text in ai_texts])/np.mean([len(word_tokenize(text)) for text in ai_texts]),
        
    }



def plot_ngram_distribution(statistics, n):
    data = []
    for category in ["Human", "AI"]:
        ngrams = statistics[f"{category} N-gram Distribution"]
        counts = [count for ngram, count in ngrams.items() if len(ngram) == n]
        data.append(counts)

    fig, ax = plt.subplots()
    ax.boxplot(data, labels=[f"{category} {n}-grams" for category in ["Human", "AI"]])
    ax.set_title(f"{n}-gram Frequency Distribution")
    plt.show()

def plot_average_text_lengths(statistics):
    data = [statistics[f"{category} Average Text Length"] for category in ["Human", "AI"]]

    fig, ax = plt.subplots()
    ax.bar(["Human", "AI"], data)
    ax.set_ylabel("Average Text Length")
    ax.set_title("Comparison of Average Text Lengths")
    plt.show()
    
def plot_average_text_Character_lengths(statistics):
    data = [statistics[f"{category} Average Text character Length"] for category in ["Human", "AI"]]

    fig, ax = plt.subplots()
    ax.bar(["Human", "AI"], data)
    ax.set_ylabel("Average Text character Length")
    ax.set_title("Comparison of Average Text character Lengths")
    plt.show()

def create_top_grams_dataframes(stat, n):
    data = []
    for category in ["Human", "AI"]:
        ngrams = stat[f"{category} N-gram Distribution"]
        top_ngrams = [item for item in ngrams.items() if len(item[0]) == n]
        top_ngrams.sort(key=lambda x: x[1], reverse=True)
        top_ngrams = top_ngrams[:10]
        data.append(pd.DataFrame(top_ngrams, columns=['ngram', 'count']))
        data[-1]['type'] = category

    return data[0], data[1]

statistics = descriptive_statistics(dataset, max_ngram_length=8)

statistics_new = descriptive_statistics(new_dataset, max_ngram_length=8)

for n in range(1, 8):
    plot_ngram_distribution(statistics, n)

plot_average_text_lengths(statistics)
plot_average_text_Character_lengths(statistics)

plot_average_text_lengths(statistics_new)
plot_average_text_Character_lengths(statistics_new)


for n in range(1, 8):
    human_df, ai_df = create_top_grams_dataframes(statistics, n)
    print(f"Top 10 {n}-grams for Human Text:")
    print(human_df)
    print(f"\nTop 10 {n}-grams for AI-generated Text:")
    print(ai_df)
    print("\n" + "="*80 + "\n")


def add_ngram_columns(dataset, max_ngram_length=3):
    for n in range(1, max_ngram_length + 1):
        dataset[f'{n}-gram Distribution'] = dataset['abstract'].apply(lambda text: ngram_distribution(text, n))
    return dataset

for n in range(1, 8):
    human_df, ai_df = create_top_grams_dataframes(statistics_new, n)
    print(f"Top 10 {n}-grams for Human Text:")
    print(human_df)
    print(f"\nTop 10 {n}-grams for AI-generated Text:")
    print(ai_df)
    print("\n" + "="*80 + "\n")




# -----------------------------------------------------Grammer -------------------------------------------------------#

# https://pypi.org/project/language-tool-python/
# pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-2.2.0/en_core_web_sm-2.2.0.tar.gz
#https://spacy.io/usage/models#download-pip
#import spacy #Tried to get it into a spacy pipline for efficiency but could not get it to work. 
import language_tool_python

tool = language_tool_python.LanguageTool('en-US')

def grammar_score(text):
    matches = tool.check(text)
    errors = len(matches)
    return errors / len(text.split())

def calculate_grammar_scores(df, text_column="abstract"):
    
    texts = df[text_column].tolist()
    grammar_scores = [grammar_score(text) for text in texts]
    df["Grammar Score"] = grammar_scores
    return df

dataset_with_perplexity = calculate_grammar_scores(dataset_with_perplexity)
new_dataset = calculate_grammar_scores(new_dataset)



plt.figure(figsize=(10, 6))
ax = sns.boxplot(x="is_ai_generated", y="Grammar Score", data=dataset_with_perplexity,showfliers = False) ##REMOVED OUTLIERS!! 
#ax = sns.boxplot(x="is_ai_generated", y="Grammar Score", data=df_with_grammar_scores)  
ax.set_xticklabels(["Human-generated", "AI-generated"])
ax.set_xlabel("Text Type")
ax.set_ylabel("Grammar Score")
ax.set_title("Grammar Score for Human-generated vs. AI-generated Text")

plt.show()


#-------------------------------------------- TTR -------------------------------------#

##TTR is the ratio obtained by dividing the types (the total number of different words) 
##occurring in a text or utterance by its tokens (the total number of words). 
##A high TTR indicates a high degree of lexical variation while a low TTR indicates the opposite.



def calculate_ttr_all_ngrams(dataset, n=2):
    ttrs = []
    for index, row in dataset.iterrows():
        text = row['abstract']
        tokens = word_tokenize(text.lower())
        text_ngrams = list(ngrams(tokens, n))
        types = set(text_ngrams)  # create a set of unique n-grams

        if len(text_ngrams) == 0:
            ttrs.append(None)
            print('none')
        else:
            unique_ngram_count = len(types)
            ttr = unique_ngram_count / len(text_ngrams)
            ttrs.append(ttr)
    
    return ttrs

def plot_ttr_histogram_ngrams(dataset, ai_generated, n=1):
    if ai_generated:
        color = 'red'
        title = f'Type-Token Ratio Histogram (AI-Generated Abstracts) - ngram={n}'
    else:
        color = 'green'
        title = f'Type-Token Ratio Histogram (Human-Generated Abstracts) - ngram={n}'

    ttrs = calculate_ttr_all_ngrams(dataset, n=n)

    plt.hist(ttrs, bins=20, color=color, edgecolor='black')
    plt.title(title)
    plt.xlabel('TTR')
    plt.ylabel('Frequency')
    plt.show()
    

# Plotting

human_abstracts = dataset.loc[dataset['is_ai_generated'] == False]
ai_abstracts = dataset.loc[dataset['is_ai_generated'] == True]

# Plot TTR histograms based on n-grams (1-5)
for n in range(1, 4):
    print(f"Plots for n-grams (n={n})")
    plot_ttr_histogram_ngrams(human_abstracts, ai_generated=False, n=n)
    plot_ttr_histogram_ngrams(ai_abstracts, ai_generated=True, n=n)

new_dataset['TTR_1ngram'] = calculate_ttr_all_ngrams(new_dataset, n=1)
new_dataset['TTR_2ngram'] = calculate_ttr_all_ngrams(new_dataset, n=2)
new_dataset['TTR_3ngram'] = calculate_ttr_all_ngrams(new_dataset, n=3)

dataset_with_perplexity['TTR_1ngram'] = calculate_ttr_all_ngrams(dataset_with_perplexity, n=1)
dataset_with_perplexity['TTR_2ngram'] = calculate_ttr_all_ngrams(dataset_with_perplexity, n=2)
dataset_with_perplexity['TTR_3ngram'] = calculate_ttr_all_ngrams(dataset_with_perplexity, n=3)




# ------------------------------------------- AVG Word Lenght -------------------------------------------------------------#

import pandas as pd
from nltk.tokenize import word_tokenize

def calculate_avg_word_length(dataset, ai_generated):
    filtered_dataset = dataset.loc[dataset['is_ai_generated'] == ai_generated]

    word_lengths = []
    for index, row in filtered_dataset.iterrows():
        text = row['abstract']
        #tokens = word_tokenize(text.lower()) #TOKENS
        tokens = text.split() # SPLIT by spaces 

        lengths = [len(token) for token in tokens]
        avg_length = sum(lengths) / len(lengths)
        word_lengths.append(avg_length)
    
    return word_lengths

human_avg_lengths = calculate_avg_word_length(dataset, ai_generated=False)
ai_avg_lengths = calculate_avg_word_length(dataset, ai_generated=True)

def calculate_avg_word_length_all(dataset):
    filtered_dataset = dataset

    word_lengths = []
    for index, row in filtered_dataset.iterrows():
        text = row['abstract']
        #tokens = word_tokenize(text.lower()) #TOKENS
        tokens = text.split() # SPLIT by spaces 

        lengths = [len(token) for token in tokens]
        avg_length = sum(lengths) / len(lengths)
        word_lengths.append(avg_length)
                
    return word_lengths

dataset_with_perplexity['Average word length'] = calculate_avg_word_length_all(dataset_with_perplexity)
new_dataset['Average word length'] = calculate_avg_word_length_all(new_dataset)


plt.hist(human_avg_lengths, bins=20, color='green', edgecolor='black')
plt.title('Average Word Length Histogram (Human-Generated Abstracts)')
plt.xlabel('Average Word Length')
plt.ylabel('Frequency')
plt.show()

plt.hist(ai_avg_lengths, bins=20, color='red', edgecolor='black')
plt.title('Average Word Length Histogram (AI-Generated Abstracts)')
plt.xlabel('Average Word Length')
plt.ylabel('Frequency')
plt.show()


#------------------------------------------------------ Frequency of function words ---------------------------------------------------#
import nltk
nltk.download('punkt')
nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_function_words(dataset):
    function_words = set(stopwords.words('english'))  # NLTK's corpus of English stopwords
    freqs = []
    
    for index, row in dataset.iterrows():
        text = row['abstract']
        tokens = word_tokenize(text.lower())
        func_word_count = sum(1 for token in tokens if token in function_words)
        freq = func_word_count / len(tokens) if tokens else 0
        freqs.append(freq)

    # Add Frequencies as a new column in the dataset
    dataset['frequency_of_function_words'] = freqs
    
    return dataset

def plot_distribution(dataset):
    # Create a copy of the dataset to avoid modifying the original one
    dataset_copy = dataset.copy()

    # Map 1 to 'AI' and 0 to 'Human'
    dataset_copy['source'] = dataset['is_ai_generated'].map({1: 'AI', 0: 'Human'})

    plt.figure(figsize=(10, 6))
    sns.boxplot(x='source', y='frequency_of_function_words', data=dataset_copy)
    plt.title('Distribution of Function Word Frequencies: AI vs Human')
    plt.show()


dataset_with_perplexity = calculate_function_words(dataset_with_perplexity)
new_dataset = calculate_function_words(new_dataset)

plot_distribution(dataset_with_perplexity)

#------------------------------------------------------ Modelling ---------------------------------------------------#

import pandas as pd
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import FunctionTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.dummy import DummyClassifier
from sklearn.naive_bayes import MultinomialNB
import string
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer



# Function for text normalization
def text_normalizer(texts, remove_stopwords=True, remove_digits=True, remove_common=True):
    custom_stopwords = ['a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 'when', 'where', 'how', 'why', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'will', 'would', 'should', 'can', 'could', 'may', 'might', 'must', 'ought', 'i', 'you', 'he', 'she', 'it', 'we', 'they']
    normalized_texts = []
    for text in texts:
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        # Remove digits
        if remove_digits:
            text = re.sub(r'\d+', '', text)
        if remove_stopwords:
            words = text.split()
            text = ' '.join([word for word in words if word not in custom_stopwords])
        if remove_common: 
            words = text.split()
            most_common = [word for word, count in Counter(words).most_common(10)]
            words = [word for word in words if word not in most_common]
            text = ' '.join(words)
        normalized_texts.append(text)
    return normalized_texts


# Split the data into training, validation, and testing sets
X = dataset["abstract"]
y = dataset["is_ai_generated"]

X_train, X_val_test, y_train, y_val_test = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_val_test, y_val_test, test_size=0.5, random_state=42)



# Create a pipeline
pipeline = Pipeline([
    ('text_normalizer', FunctionTransformer(text_normalizer, validate=False)),
    ('tfidf', TfidfVectorizer()),
    ('classifier', LogisticRegression())
])

# Define the parameter grid for GridSearchCV

# tfidf__max_df -- Ignores terms that appear in more than 90% or 100% of the documents --> is used to remove terms that appear too frequently, also know as corpus-specific stop words
# 'tfidf__ngram_range' -- The lower and upper boundry of the range if n-values for different n-grams. fx 1,2 means uni and bi grams 
# Logistic C values -- Inverse reguliarization strengh: used to reduce the complexity of the prectition function: makes the model simpler. High c means we trust training data 
# Classifier penalty / solver Logistic Regression - we use L2 (ridge) - In the Lasso method, the coefficients can be reduced to exactly zero, while in the Ridge method, they are only made smaller but not reduced to zero.
# Random forrest - N estimator - the number of trees in the forest (default 100) / Max depth - the maxiumum depth of trees, 
# Dummy classifier only one strategy as this is a baseline method - most frequent
# MultinomialNB Naive bayes - Alpha - smoothing parameter - set to default, used to handle zero probablity instances 
param_grid = [
    {
        'tfidf__max_df': [0.9, 1.0],
        'tfidf__ngram_range': [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
        'classifier': [LogisticRegression()],
        'classifier__C': [0.1, 1, 10],
        'classifier__penalty': ['l2','l1'],
        'classifier__solver': ['liblinear']
    },
    {
        'tfidf__max_df': [0.9, 1.0],
        'tfidf__ngram_range': [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
        'classifier': [RandomForestClassifier()],
        'classifier__n_estimators': [50, 100, 200],
        'classifier__max_depth': [None, 20, 50, 100],
        'classifier__min_samples_split': [10,50,100]
    },
    {
        'classifier': [DummyClassifier()],
        'classifier__strategy': ['most_frequent','uniform']
    },
    {
        'tfidf__max_df': [0.9, 1.0],
        'tfidf__ngram_range': [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
        'classifier': [MultinomialNB()]
    }
]

# Perform a grid search with cross-validation #high presision
grid_search = GridSearchCV(pipeline, param_grid, scoring='precision', cv=5, n_jobs=-1,verbose=5)
grid_search.fit(X_train, y_train)

# Print the best combination of hyperparameters
print("Best parameters: ", grid_search.best_params_)


from sklearn.metrics import precision_score, recall_score, accuracy_score, f1_score
# Define the models and their parameters
models = [
    {
     'name': 'Random Forest',
     'params': {'classifier': RandomForestClassifier(max_depth=None, min_samples_split=10, n_estimators=50),'tfidf__ngram_range': (5, 6),'tfidf__max_df': 0.9 }
     },
    {
     'name': 'Logistic Regression',
     'params': {'classifier': LogisticRegression(C=0.1, penalty='l1', solver='liblinear'),'tfidf__ngram_range': (5, 6),'tfidf__max_df': 0.9}
     },
    {
     'name': 'Dummy Classifier',
     'params': {'classifier': DummyClassifier(strategy='uniform')}
     },
    {
     'name': 'MultinomialNB',
     'params': {'classifier': MultinomialNB(),'tfidf__ngram_range': (6, 7),'tfidf__max_df': 0.9}
     }
]



# Split the data into train, validation, and test sets
X_train, X_val_test, y_train, y_val_test = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_val_test, y_val_test, test_size=0.5, random_state=42)



# Create a pandas DataFrame to store the results
results_df = pd.DataFrame(columns=['Model', 'Set', 'Accuracy', 'Precision', 'Recall', 'F1-score'])



# Function to evaluate a model and store the results in the DataFrame
def evaluate_model(model_name, model, X, y, set_name):
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    precision = precision_score(y, y_pred)
    recall = recall_score(y, y_pred)
    f1 = f1_score(y, y_pred)

    results_df.loc[len(results_df)] = [model_name, set_name, accuracy, precision, recall, f1]



# Iterate over each model and evaluate them on the train, validation, and test sets
for model_info in models:
    model_name = model_info['name']
    model_params = model_info['params']
    model = model_params['classifier']

    # Train the model
    model.fit(X_train, y_train)

    # Evaluate on the train set
    evaluate_model(model_name, model, X_train, y_train, 'Train')

    # Evaluate on the validation set
    evaluate_model(model_name, model, X_val, y_val, 'Validation')

    # Evaluate on the test set
    evaluate_model(model_name, model, X_test, y_test, 'Test')



# Print the results
print(results_df)

# Evaluate the model on Train data
y_train_pred = grid_search.predict(X_train)
print("Validation Classification Report:\n", classification_report(y_train, y_train_pred))

# Evaluate the model on  data
y_val_pred = grid_search.predict(X_val)
print("Validation Classification Report:\n", classification_report(y_val, y_val_pred))

results = grid_search.cv_results_
# Initialize empty lists for each model
rf_params = []
lr_params = []
dummy_params = []
Multi_params = []

# Loop over each set of parameters in the GridSearchCV results
for i, params in enumerate(results["params"]):
    if isinstance(params["classifier"], RandomForestClassifier):
        # Add the best parameters for the Random Forest model to the list
        best_params = {"params": params, "mean_test_score": results["mean_test_score"][i]}
        rf_params.append(best_params)
    elif isinstance(params["classifier"], LogisticRegression):
        # Add the best parameters for the Logistic Regression model to the list
        best_params = {"params": params, "mean_test_score": results["mean_test_score"][i]}
        lr_params.append(best_params)
    elif isinstance(params["classifier"], DummyClassifier):
        # Add the best parameters for the Dummy Classifier model to the list
        best_params = {"params": params, "mean_test_score": results["mean_test_score"][i]}
        dummy_params.append(best_params)
    elif isinstance(params["classifier"], MultinomialNB):
        # Add the best parameters for the Dummy Classifier model to the list
        best_params = {"params": params, "mean_test_score": results["mean_test_score"][i]}
        Multi_params.append(best_params)

# Sort the best parameters by mean test score in descending order
rf_params = sorted(rf_params, key=lambda x: x["mean_test_score"], reverse=True)[:1]
lr_params = sorted(lr_params, key=lambda x: x["mean_test_score"], reverse=True)[:1]
dummy_params = sorted(dummy_params, key=lambda x: x["mean_test_score"], reverse=True)[:1]
Multi_params = sorted(Multi_params, key=lambda x: x["mean_test_score"], reverse=True)[:1]

# Create a DataFrame with the best parameters for each model
best_params_df = pd.DataFrame({
    "model": ["Random Forest", "Logistic Regression", "Dummy Classifier", "MultinomialNB"],
    "best_params": [rf_params[0]["params"], lr_params[0]["params"], dummy_params[0]["params"],Multi_params[0]["params"]],
    "mean_test_score": [rf_params[0]["mean_test_score"], lr_params[0]["mean_test_score"], dummy_params[0]["mean_test_score"], Multi_params[0]["mean_test_score"]]
})

print(best_params_df)

best_estimator = grid_search.best_estimator_
print(best_estimator.named_steps['classifier'])

# Extract the feature importances from the Random Forest Classifier
if isinstance(best_estimator.named_steps['classifier'], RandomForestClassifier):
    rf = best_estimator.named_steps['classifier']
    feature_importances = pd.Series(rf.feature_importances_, index=best_estimator.named_steps['tfidf'].get_feature_names_out())
    feature_importances.nlargest(20).plot(kind='barh')

if isinstance(best_estimator.named_steps['classifier'], LogisticRegression):
    lr = best_estimator.named_steps['classifier']
    feature_importances = pd.Series(lr.coef_[0], index=best_estimator.named_steps['tfidf'].get_feature_names_out())
    feature_importances.nlargest(20).plot(kind='barh')

if isinstance(best_estimator.named_steps['classifier'], MultinomialNB):
    nb = best_estimator.named_steps['classifier']
    feature_probabilities = pd.DataFrame(nb.feature_log_prob_.T, columns=['class_0', 'class_1'], index=best_estimator.named_steps['tfidf'].get_feature_names_out())
    feature_probabilities['diff'] = feature_probabilities['class_1'] - feature_probabilities['class_0']
    feature_probabilities.nlargest(20, 'diff').plot(kind='barh')

if isinstance(best_estimator.named_steps['classifier'], DummyClassifier):
    feature_importances = pd.Series([1], index=['dummy'])
    feature_importances.plot(kind='barh')
    
    

# Import additional modules
from sklearn.base import clone

# Get the best configurations for each model from the grid search
best_params = grid_search.cv_results_['params'][grid_search.best_index_]

# Split the data into train, validation, and test sets
X_train, X_val_test, y_train, y_val_test = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_val_test, y_val_test, test_size=0.5, random_state=42)

# Create a pandas DataFrame to store the results
results_df = pd.DataFrame(columns=['Model', 'Set', 'Accuracy', 'Precision', 'Recall', 'F1-score'])

# Function to evaluate a model and store the results in the DataFrame
def evaluate_model(model_name, model, X, y, set_name):
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    precision = precision_score(y, y_pred)
    recall = recall_score(y, y_pred)
    f1 = f1_score(y, y_pred)

    results_df.loc[len(results_df)] = [model_name, set_name, accuracy, precision, recall, f1]

# Iterate over each model and evaluate them on the train, validation, and test sets
for model_info in models:
    model_name = model_info['name']
    model_params = best_params[model_name] if model_name in best_params else {}

    pipeline = Pipeline([
        ('text_normalizer', FunctionTransformer(text_normalizer, validate=False)),
        ('tfidf', TfidfVectorizer(max_df=model_params.get('tfidf__max_df', 1.0), 
                                  ngram_range=model_params.get('tfidf__ngram_range', (1,1)))),
        ('classifier', clone(model_info['params']['classifier']).set_params(**model_params))
    ])

    # Train the model
    pipeline.fit(X_train, y_train)

    # Evaluate on the train set
    evaluate_model(model_name, pipeline, X_train, y_train, 'Train')

    # Evaluate on the validation set
    evaluate_model(model_name, pipeline, X_val, y_val, 'Validation')

    # Evaluate on the test set
    evaluate_model(model_name, pipeline, X_test, y_test, 'Test')

# Print the results
print(results_df)


#------------------------------------------------------ Modelling without text---------------------------------------------------#

import pandas as pd
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import FunctionTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.dummy import DummyClassifier
from sklearn.naive_bayes import MultinomialNB
import string
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Split the data into training, validation, and testing sets
X = dataset_with_perplexity[['frequency_of_function_words', 'Average word length', 'TTR_1ngram','TTR_2ngram','TTR_3ngram', 'Grammar Score', 'Perplexity']]
y = dataset_with_perplexity["is_ai_generated"]


X_train, X_val_test, y_train, y_val_test = train_test_split(X, y, test_size=0.3, random_state=45)
X_val, X_test, y_val, y_test = train_test_split(X_val_test, y_val_test, test_size=0.5, random_state=45)


# Create a pipeline
pipeline = Pipeline([
    ('classifier', LogisticRegression())
])

# Define the parameter grid for GridSearchCV

# tfidf__max_df -- Ignores terms that appear in more than 90% or 100% of the documents --> is used to remove terms that appear too frequently, also know as corpus-specific stop words
# 'tfidf__ngram_range' -- The lower and upper boundry of the range if n-values for different n-grams. fx 1,2 means uni and bi grams 
# Logistic C values -- Inverse reguliarization strengh: used to reduce the complexity of the prectition function: makes the model simpler. High c means we trust training data 
# Classifier penalty / solver Logistic Regression - we use L2 (ridge) - In the Lasso method, the coefficients can be reduced to exactly zero, while in the Ridge method, they are only made smaller but not reduced to zero.
# Random forrest - N estimator - the number of trees in the forest (default 100) / Max depth - the maxiumum depth of trees, 
# Dummy classifier only one strategy as this is a baseline method - most frequent
# MultinomialNB Naive bayes - Alpha - smoothing parameter - set to default, used to handle zero probablity instances 
param_grid = [
    {
        'classifier': [LogisticRegression()],
        'classifier__C': [0.1, 1, 10],
        'classifier__penalty': ['l2','l1'],
        'classifier__solver': ['liblinear']
    },
    {
        'classifier': [RandomForestClassifier()],
        'classifier__n_estimators': [10,20, 50, 100],
        'classifier__max_depth': [None, 1,10,20,50,80,100],
        'classifier__min_samples_split': [10,50,100]
    },
    {
        'classifier': [DummyClassifier()],
        'classifier__strategy': ['most_frequent','uniform']
    },
    {
        'classifier': [MultinomialNB()]
    }
]

# Perform a grid search with cross-validation #high presision
grid_search = GridSearchCV(pipeline, param_grid, scoring='precision', cv=5, n_jobs=-1,verbose=5)
grid_search.fit(X_train, y_train)

# Print the best combination of hyperparameters
print("Best parameters: ", grid_search.best_params_)






# Evaluate the model on Train data
y_train_pred = grid_search.predict(X_train)
print("Validation Classification Report:\n", classification_report(y_train, y_train_pred))

# Evaluate the model on  data
y_val_pred = grid_search.predict(X_val)
print("Validation Classification Report:\n", classification_report(y_val, y_val_pred))

results = grid_search.cv_results_
# Initialize empty lists for each model
rf_params = []
lr_params = []
dummy_params = []
Multi_params = []

# Loop over each set of parameters in the GridSearchCV results
for i, params in enumerate(results["params"]):
    if isinstance(params["classifier"], RandomForestClassifier):
        # Add the best parameters for the Random Forest model to the list
        best_params = {"params": params, "mean_test_score": results["mean_test_score"][i]}
        rf_params.append(best_params)
    elif isinstance(params["classifier"], LogisticRegression):
        # Add the best parameters for the Logistic Regression model to the list
        best_params = {"params": params, "mean_test_score": results["mean_test_score"][i]}
        lr_params.append(best_params)
    elif isinstance(params["classifier"], DummyClassifier):
        # Add the best parameters for the Dummy Classifier model to the list
        best_params = {"params": params, "mean_test_score": results["mean_test_score"][i]}
        dummy_params.append(best_params)
    elif isinstance(params["classifier"], MultinomialNB):
        # Add the best parameters for the Dummy Classifier model to the list
        best_params = {"params": params, "mean_test_score": results["mean_test_score"][i]}
        Multi_params.append(best_params)

# Sort the best parameters by mean test score in descending order
rf_params = sorted(rf_params, key=lambda x: x["mean_test_score"], reverse=True)[:1]
lr_params = sorted(lr_params, key=lambda x: x["mean_test_score"], reverse=True)[:1]
dummy_params = sorted(dummy_params, key=lambda x: x["mean_test_score"], reverse=True)[:1]
Multi_params = sorted(Multi_params, key=lambda x: x["mean_test_score"], reverse=True)[:1]

# Create a DataFrame with the best parameters for each model
best_params_df = pd.DataFrame({
    "model": ["Random Forest", "Logistic Regression", "Dummy Classifier", "MultinomialNB"],
    "best_params": [rf_params[0]["params"], lr_params[0]["params"], dummy_params[0]["params"],Multi_params[0]["params"]],
    "mean_test_score": [rf_params[0]["mean_test_score"], lr_params[0]["mean_test_score"], dummy_params[0]["mean_test_score"], Multi_params[0]["mean_test_score"]]
})

print(best_params_df)

best_estimator = grid_search.best_estimator_
print(best_estimator.named_steps['classifier'])
index=X.columns

# Extract the feature importances from the Random Forest Classifier
if isinstance(best_estimator.named_steps['classifier'], RandomForestClassifier):
    rf = best_estimator.named_steps['classifier']
    feature_importances = pd.Series(rf.feature_importances_, index=X.columns)
    feature_importances.nlargest(20).plot(kind='barh')

if isinstance(best_estimator.named_steps['classifier'], LogisticRegression):
    lr = best_estimator.named_steps['classifier']
    feature_importances = pd.Series(lr.coef_[0], index=X.columns)
    feature_importances.nlargest(20).plot(kind='barh')
    
if isinstance(best_estimator.named_steps['classifier'], MultinomialNB):
    nb = best_estimator.named_steps['classifier']
    feature_probabilities = pd.DataFrame(nb.feature_log_prob_.T, columns=['class_0', 'class_1'], index=best_estimator.named_steps['tfidf'].get_feature_names_out())
    feature_probabilities['diff'] = feature_probabilities['class_1'] - feature_probabilities['class_0']
    feature_probabilities.nlargest(20, 'diff').plot(kind='barh')

if isinstance(best_estimator.named_steps['classifier'], DummyClassifier):
    feature_importances = pd.Series([1], index=['dummy'])
    feature_importances.plot(kind='barh')
    


from sklearn.metrics import precision_score, recall_score, f1_score, accuracy_score

# Define the models and their parameters
models = [
    {
     'name': 'Random Forest',
     'params': {'classifier': RandomForestClassifier(max_depth=50, min_samples_split=10, n_estimators=20)}
     },
    {
     'name': 'Logistic Regression',
     'params': {'classifier': LogisticRegression(C=10, penalty='l1', solver='liblinear')}
     },
    {
     'name': 'Dummy Classifier',
     'params': {'classifier': DummyClassifier(strategy='uniform')}
     },
    {
     'name': 'MultinomialNB',
     'params': {'classifier': MultinomialNB()}
     }
]


# Split the data into train, validation, and test sets
X_train, X_val_test, y_train, y_val_test = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_val_test, y_val_test, test_size=0.5, random_state=42)



# Create a pandas DataFrame to store the results
results_df = pd.DataFrame(columns=['Model', 'Set', 'Accuracy', 'Precision', 'Recall', 'F1-score'])



# Function to evaluate a model and store the results in the DataFrame
def evaluate_model(model_name, model, X, y, set_name):
    y_pred = model.predict(X)
    accuracy = accuracy_score(y, y_pred)
    precision = precision_score(y, y_pred)
    recall = recall_score(y, y_pred)
    f1 = f1_score(y, y_pred)

    results_df.loc[len(results_df)] = [model_name, set_name, accuracy, precision, recall, f1]



# Iterate over each model and evaluate them on the train, validation, and test sets
for model_info in models:
    model_name = model_info['name']
    model_params = model_info['params']
    model = model_params['classifier']

    # Train the model
    model.fit(X_train, y_train)

    # Evaluate on the train set
    evaluate_model(model_name, model, X_train, y_train, 'Train')

    # Evaluate on the validation set
    evaluate_model(model_name, model, X_val, y_val, 'Validation')

    # Evaluate on the test set
    evaluate_model(model_name, model, X_test, y_test, 'Test')



# Print the results
print(results_df)    

#------------------------------------------------------ Plot for paper with text ---------------------------------------------------#
    
# Your text_normalizer function here...
# Split the data into training, validation, and testing sets
X = dataset["abstract"]
y = dataset["is_ai_generated"]

X_train, X_val_test, y_train, y_val_test = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_val_test, y_val_test, test_size=0.5, random_state=42)


# Create a pipeline
pipeline = Pipeline([
    ('text_normalizer', FunctionTransformer(text_normalizer, validate=False)),
    ('tfidf', TfidfVectorizer()),
    ('classifier', LogisticRegression())
])


# Define your logistic regression parameters here:
logistic_params = {
    'classifier__C': 0.1,       # For example
    'classifier__penalty': 'l2',
    'classifier__solver': 'liblinear'
}


# Set the parameters in your classifier
pipeline.set_params(**logistic_params)

# Train the model
pipeline.fit(X_train, y_train)

# Predict the classes and probabilities on the test set
y_pred = pipeline.predict(X_test)
y_pred_proba = pipeline.predict_proba(X_test)

# Evaluate the model
print("Test Classification Report:\n", classification_report(y_test, y_pred))

# If you want to extract feature importances for Logistic Regression
lr = pipeline.named_steps['classifier']
feature_importances = pd.Series(lr.coef_[0], index=pipeline.named_steps['tfidf'].get_feature_names_out())
feature_importances.nlargest(20).plot(kind='barh')



import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import pandas as pd
import matplotlib.pyplot as plt

# Split the data into train, validation, and test sets
X_train, X_val_test, y_train, y_val_test = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_val_test, y_val_test, test_size=0.5, random_state=42)

# Create separate test sets for AI and human-generated texts
X_test_ai = X_test[y_test == 1]
X_test_human = X_test[y_test == 0]

# Predict probabilities using the pipeline for each set
y_pred_proba_ai = pipeline.predict_proba(X_test_ai)[:, 1]
y_pred_proba_human = pipeline.predict_proba(X_test_human)[:, 1]

# Create random noise
noise_ai = np.random.normal(1, 0.1, len(y_pred_proba_ai))
noise_human = np.random.normal(0, 0.10, len(y_pred_proba_human))

# Prepare data for the plot
ai_df = pd.DataFrame({'Generated By': noise_ai, 'Probability': y_pred_proba_ai})  # 1 for AI
human_df = pd.DataFrame({'Generated By': noise_human, 'Probability': y_pred_proba_human})  # 0 for Human

# Concatenate the dataframes
plot_df = pd.concat([ai_df, human_df])

# Generate plot
plt.figure(figsize=(10, 6))
plt.scatter(plot_df['Generated By'], plot_df['Probability'], c=plot_df['Generated By'], alpha=0.5, cmap='viridis')

plt.title('Prediction Probabilities for AI vs. Human Generated Text')
plt.xlabel('Generated By (1=AI, 0=Human)')
plt.ylabel('Probability')
plt.xticks([0, 1])  # Ensuring only 0 and 1 are shown on the x-axis
plt.show()



#------------------------------------------------------ Plot for paper without text ---------------------------------------------------#


import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import pandas as pd
import matplotlib.pyplot as plt

# Split the data into train, validation, and test sets
X_train, X_val_test, y_train, y_val_test = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_val_test, y_val_test, test_size=0.5, random_state=42)

# Create separate test sets for AI and human-generated texts
X_test_ai = X_test[y_test == 1]
X_test_human = X_test[y_test == 0]

# Predict probabilities using the pipeline for each set
y_pred_proba_ai = grid_search.best_estimator_.predict_proba(X_test_ai)[:, 1]
y_pred_proba_human = grid_search.best_estimator_.predict_proba(X_test_human)[:, 1]

# Create random noise
noise_ai = np.random.normal(1, 0.1, len(y_pred_proba_ai))
noise_human = np.random.normal(0, 0.10, len(y_pred_proba_human))

# Prepare data for the plot
ai_df = pd.DataFrame({'Generated By': noise_ai, 'Probability': y_pred_proba_ai})  # 1 for AI
human_df = pd.DataFrame({'Generated By': noise_human, 'Probability': y_pred_proba_human})  # 0 for Human

# Concatenate the dataframes
plot_df = pd.concat([ai_df, human_df])

# Generate plot
plt.figure(figsize=(10, 6))
plt.scatter(plot_df['Generated By'], plot_df['Probability'], c=plot_df['Generated By'], alpha=0.5, cmap='viridis')

plt.title('Prediction Probabilities for AI vs. Human Generated Text')
plt.xlabel('Generated By (1=AI, 0=Human)')
plt.ylabel('Probability')
plt.xticks([0, 1])  # Ensuring only 0 and 1 are shown on the x-axis
plt.show()


#------------------------------------------------------ new dataset ---------------------------------------------------#

X = new_dataset[['frequency_of_function_words', 'Average word length', 'TTR_1ngram','TTR_2ngram','TTR_3ngram', 'Grammar Score', 'Perplexity']]
y = new_dataset["is_ai_generated"]

# Create separate test sets for AI and human-generated texts
X_test_ai = X[y == 1]
X_test_human = X[y == 0]

# Predict probabilities using the pipeline for each set
y_pred_proba_ai = grid_search.best_estimator_.predict_proba(X_test_ai)[:, 1]
y_pred_proba_human = grid_search.best_estimator_.predict_proba(X_test_human)[:, 1]

# Create random noise
noise_ai = np.random.normal(1, 0.1, len(y_pred_proba_ai))
noise_human = np.random.normal(0, 0.10, len(y_pred_proba_human))

# Prepare data for the plot
ai_df = pd.DataFrame({'Generated By': noise_ai, 'Probability': y_pred_proba_ai})  # 1 for AI
human_df = pd.DataFrame({'Generated By': noise_human, 'Probability': y_pred_proba_human})  # 0 for Human

# Concatenate the dataframes
plot_df = pd.concat([ai_df, human_df])

# Generate plot
plt.figure(figsize=(10, 6))
plt.scatter(plot_df['Generated By'], plot_df['Probability'], c=plot_df['Generated By'], alpha=0.5, cmap='viridis')

plt.title('Prediction Probabilities for AI vs. Human Generated Text')
plt.xlabel('Generated By (1=AI, 0=Human)')
plt.ylabel('Probability')
plt.xticks([0, 1])  # Ensuring only 0 and 1 are shown on the x-axis
plt.show()




#------------------------------------------------------ DistilBert ---------------------------------------------------#


from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments, logging

logging.set_verbosity_info()



# define features and target
X = dataset["abstract"]
y = dataset["is_ai_generated"]
x_1 = new_dataset["abstract"]
y_1 = new_dataset["is_ai_generated"]

# split into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# initialize tokenizer
tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')

# tokenize the datasets
train_encodings = tokenizer(list(X_train), truncation=True, padding=True)
test_encodings = tokenizer(list(X_test), truncation=True, padding=True)
test_1 = tokenizer(list(x_1), truncation=True, padding=True)

# convert datasets into the HuggingFace's format
class AI_Dataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

train_dataset = AI_Dataset(train_encodings, list(y_train))
test_dataset = AI_Dataset(test_encodings, list(y_test))
test_1dataset = AI_Dataset(test_encodings, list(y_1))

# initialize the model
model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased')



# define the training arguments
training_args = TrainingArguments(
    output_dir='./results',          # output directory
    num_train_epochs=3,              # total number of training epochs
    per_device_train_batch_size=16,  # batch size per device during training
    per_device_eval_batch_size=64,   # batch size for evaluation
    warmup_steps=500,                # number of warmup steps for learning rate scheduler
    weight_decay=0.01,               # strength of weight decay
    logging_dir='./logs',            # directory for storing logs
    logging_steps=1,
)

# create the trainer and train the model
trainer = Trainer(
    model=model,                         # the instantiated 🤗 Transformers model to be trained
    args=training_args,                  # training arguments, defined above
    train_dataset=train_dataset,         # training dataset
    eval_dataset=test_dataset            # evaluation dataset
)

trainer.train()


trainer.evaluate()
predictions = trainer.predict(test_1dataset)

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Get the predictions
predictions, _, _ = trainer.predict(test_1dataset)

# Pick the class with the highest score as our predicted class
pred_labels = np.argmax(predictions, axis=1)

# Calculate and print the metrics
accuracy = accuracy_score(y_1, pred_labels)
precision = precision_score(y_1, pred_labels, average='weighted')
recall = recall_score(y_1, pred_labels, average='weighted')
f1 = f1_score(y_1, pred_labels, average='weighted')

print(f'Accuracy: {accuracy}')
print(f'Precision: {precision}')
print(f'Recall: {recall}')
print(f'F1 Score: {f1}')


import numpy as np
import matplotlib.pyplot as plt
from scipy.special import softmax

# Calculate probabilities from logits
probabilities = softmax(predictions, axis=1)

# Get probabilities of the positive class (AI-generated)
prob_AI = probabilities[:, 1]

# Create boolean arrays for AI-generated and human-written texts
is_AI = np.array(y_1) == 1
is_human = np.array(y_1) == 0

# Create random noise
noise_AI = np.random.normal(1, 0.1, sum(is_AI))
noise_human = np.random.normal(0, 0.1, sum(is_human))

# Prepare data for the plot
prob_AI_human = np.concatenate([prob_AI[is_AI], prob_AI[is_human]])
generated_by = np.concatenate([noise_AI, noise_human])

# Generate plot
plt.figure(figsize=(10, 6))
plt.scatter(generated_by, prob_AI_human, c=generated_by, alpha=0.5, cmap='viridis')

plt.title('Prediction Probabilities for AI vs. Human Generated Text')
plt.xlabel('Generated By (1=AI, 0=Human)')
plt.ylabel('Probability')
plt.xticks([0, 1])  # Ensuring only 0 and 1 are shown on the x-axis
plt.show()




#------------------------------------------------------ Neural network ---------------------------------------------------#



import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Set random seed for reproducibility
torch.manual_seed(42)

# Prepare the dataset
# Assuming you have a dataset variable containing the preprocessed feature-based dataset
X = dataset_with_perplexity[['Perplexity', 'Grammar Score', 'Average word length', 'frequency_of_function_words', 'TTR_1ngram', 'TTR_2ngram', 'TTR_3ngram']].values
y = dataset_with_perplexity['is_ai_generated'].values

# Split the dataset into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Convert the data to PyTorch tensors
X_train = torch.FloatTensor(X_train)
y_train = torch.LongTensor(y_train)
X_test = torch.FloatTensor(X_test)
y_test = torch.LongTensor(y_test)

# Define the neural network model
class FeatureBasedModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super(FeatureBasedModel, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)  # Additional hidden layer
        self.fc3 = nn.Linear(hidden_dim, output_dim)  # Input dimension is now hidden_dim
        self.relu = nn.ReLU()
        self.softmax = nn.Softmax(dim=1)
    
    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)  # Pass output through additional hidden layer
        out = self.relu(out)
        out = self.fc3(out)
        out = self.softmax(out)
        return out
# Set the dimensions for input, hidden, and output layers
input_dim = X_train.shape[1]
hidden_dim = 128
output_dim = 2  # Binary classification: AI-generated or human-generated

# Instantiate the model
model = FeatureBasedModel(input_dim, hidden_dim, output_dim)

# Define the loss function and optimizer
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.0001)

# Training loop
num_epochs = 100
for epoch in range(num_epochs):
    # Forward pass
    outputs = model(X_train)
    loss = criterion(outputs, y_train)
    
    # Backward and optimize
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

# Evaluation
model.eval()
with torch.no_grad():
    # Predict on the test set
    outputs = model(X_test)
    _, predicted = torch.max(outputs.data, 1)
    
    # Calculate evaluation metrics
    accuracy = accuracy_score(y_test, predicted)
    precision = precision_score(y_test, predicted)
    recall = recall_score(y_test, predicted)
    f1 = f1_score(y_test, predicted)

# Print the evaluation results
print("Evaluation results:")
print("Accuracy:", accuracy)
print("Precision:", precision)
print("Recall:", recall)
print("F1 Score:", f1)
    


import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

# Predict probabilities using the model for each set
model.eval()
with torch.no_grad():
    outputs_ai = model(torch.FloatTensor(X_test[y_test == 1]))
    outputs_human = model(torch.FloatTensor(X_test[y_test == 0]))

# Get the probabilities of the positive class (AI-generated)
y_pred_proba_ai = outputs_ai[:, 1].numpy()
y_pred_proba_human = outputs_human[:, 1].numpy()

# Create random noise
noise_ai = np.random.normal(1, 0.1, len(y_pred_proba_ai))
noise_human = np.random.normal(0, 0.10, len(y_pred_proba_human))

# Prepare data for the plot
ai_df = pd.DataFrame({'Generated By': noise_ai, 'Probability': y_pred_proba_ai})  # 1 for AI
human_df = pd.DataFrame({'Generated By': noise_human, 'Probability': y_pred_proba_human})  # 0 for Human

# Concatenate the dataframes
plot_df = pd.concat([ai_df, human_df])

# Generate plot
plt.figure(figsize=(10, 6))
plt.scatter(plot_df['Generated By'], plot_df['Probability'], c=plot_df['Generated By'], alpha=0.5, cmap='viridis')

plt.title('Prediction Probabilities for AI vs. Human Generated Text')
plt.xlabel('Generated By (1=AI, 0=Human)')
plt.ylabel('Probability')
plt.xticks([0, 1])  # Ensuring only 0 and 1 are shown on the x-axis
plt.show()



