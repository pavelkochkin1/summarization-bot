import pytorch_lightning as pl
from transformers import T5ForConditionalGeneration, T5TokenizerFast as T5Tokenizer
import argparse

class SummaryModel(pl.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = T5ForConditionalGeneration.from_pretrained("t5-base", return_dict=True)
    
class Model():
    def __init__(self):
        self.tokenizer = T5Tokenizer.from_pretrained("t5-base")
        self.model = SummaryModel()
        self.model.load_from_checkpoint("pre-trained.ckpt")
    
    def summarize(self, text:str) -> str:
        text_encoding = self.tokenizer(
            text,
            max_length=512,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            add_special_tokens=True,
            return_tensors="pt"
        )

        generated_ids = self.model.model.generate(
        input_ids = text_encoding["input_ids"],
        attention_mask = text_encoding["attention_mask"],
        max_length=200,
        num_beams=2,
        repetition_penalty=2.5,
        length_penalty = 1.0,
        early_stopping = True
        )

        preds = [
        self.tokenizer.decode(gen_id, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        for gen_id in generated_ids
        ]

        return "".join(preds)