from role_play_synthetic.models.base import Model
import openai


class OpenAIModel(Model):

    def __init__(self, model_name="gpt-3.5-turbo"):
        super(OpenAIModel, self).__init__()
        self.model_name = model_name

    def generate(self, prompt: str, generation_params: dict):
        completion = openai.ChatCompletion.create(
            model=self.model_name,
            messages=prompt,
            **generation_params
        )
        response = completion.choices[0].message.content
        return response.strip()
