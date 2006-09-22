
def Upper( text ):
	return " ".join([w[0].upper() + w[1:].lower() for w in text.split()])

def escapeHTML( text ):
	text = text.replace("&", "&amp;")
	text = text.replace(">", "&gt;")
	text = text.replace("<", "&lt;")
	return text

