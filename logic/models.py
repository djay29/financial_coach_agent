from pydantic import Field, BaseModel

class ClassifiedOutput(BaseModel):
    Payment_Mode : str  = Field(description="The Mode of the payment")
    Merchant_Name :  str = Field(description="The Name of the Merchant")
    Category : str = Field(description="The Expense category")
