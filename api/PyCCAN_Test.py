from api.PyCCAN_ExpressionEvaluator import ExpressionEvaluator


evaluator = ExpressionEvaluator()

text_expressions = []
text_expressions.append( ["3+4",7])
text_expressions.append( ["8/4/2",1])
text_expressions.append( ["3-7*2+4",-7])
text_expressions.append( ['"Hallo"+" " + "hier ist"',"Hallo hier ist"])
text_expressions.append( ["3-7*2+4-dummy + 5*unknown_alias",-3]) # alias are mapped to value 1
     
for tuple in text_expressions:
    expression = tuple[0]
    solution   = tuple[1]
    
    result = evaluator.resolve(expression)
    print(expression + " = " + str(result))
    if result != solution:
        print("Error")


text_expressions = []
text_expressions.append(["3+ EVENT::param1",None])
text_expressions.append( ["3-7*2+4-EVENT::dummy + 5*unknown_alias",-3]) # alias are mapped to value 1
text_expressions.append( ["3-7*2+4-EVENT::dummy + 5*deivce::status1",-3])
for tuple in text_expressions:
    expression = tuple[0]
    solution   = tuple[1]
    result = evaluator.resolve(expression)
    print(result)

print("ended")