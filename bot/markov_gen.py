import markovify

with open("markov.txt", "r", encoding="utf-8") as f:
    text = f.read()
model = markovify.Text(text)

def generate_markov_text(sentences=5):
    result = []
    for _ in range(sentences):
        sentence = model.make_sentence(tries=100)
        if sentence:
            result.append(sentence)
    return " ".join(result)