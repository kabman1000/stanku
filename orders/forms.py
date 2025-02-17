from django import forms
from .models import Order

class StockHistorySearchForm(forms.ModelForm):
	start_date = forms.DateTimeField(required=False,widget=forms.DateInput(attrs={'class':'datetimeinput'}))
	end_date = forms.DateTimeField(required=False,widget=forms.DateInput(attrs={'class':'datetimeinput'}))

	class Meta:
		model = Order
		fields = ['start_date', 'end_date']