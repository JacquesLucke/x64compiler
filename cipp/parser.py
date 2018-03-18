from . import ast
from . lexer import Lexer
from . token_stream import TokenStream

from . tokens import (
    createSingleCharToken,
    IdentifierToken, IntegerToken,
    CommentToken, WhitespaceToken
)

SingleCharToken = createSingleCharToken("(){}[],=+-*/@;<>!")
cippLexer = Lexer(
    [IdentifierToken, IntegerToken, CommentToken, 
     SingleCharToken, WhitespaceToken], 
    ignoredTokens = [WhitespaceToken, CommentToken]
)

def astFromString(string):
    tokens = stringToTokenStream(string)
    return parseProgram(tokens)

def stringToTokenStream(string):
    return TokenStream(cippLexer.tokenize(string))

def parseProgram(tokens):
    functions = []
    while nextIsKeyword(tokens, "def"):
        function = parseFunction(tokens)
        functions.append(function)
    return ast.ProgramAST(functions)

def parseFunction(tokens):
    acceptKeyword(tokens, "def")
    retType = parseType(tokens)
    acceptLetter(tokens, "@")
    name = acceptIdentifier(tokens)
    arguments = parseArguments(tokens)
    statement = parseStatement(tokens)
    return ast.FunctionAST(name, retType, arguments, statement)

def parseArguments(tokens):
    acceptLetter(tokens, "(")
    if nextIsLetter(tokens, ")"):
        acceptLetter(tokens, ")")
        return []
    else:
        arguments = []
        while True:
            argument = parseArgument(tokens)
            arguments.append(argument)
            if nextIsLetter(tokens, ","):
                acceptLetter(tokens, ",")
                continue
            else:
                break
        acceptLetter(tokens, ")")
        return arguments

def parseArgument(tokens):
    dataType = parseType(tokens)
    name = acceptIdentifier(tokens)
    return ast.ArgumentAST(name, dataType)

def parseType(tokens):
    dataType = acceptIdentifier(tokens)
    return ast.TypeAST(dataType)

def parseStatement(tokens):
    if nextIsLetter(tokens, "{"):
        return parseStatement_Block(tokens)
    elif nextIsKeyword(tokens, "return"):
        return parseStatement_Return(tokens)
    elif nextIsKeyword(tokens, "let"):
        return parseStatement_Let(tokens)
    elif nextIsKeyword(tokens, "while"):
        return parseStatement_While(tokens)
    elif nextIsKeyword(tokens, "if"):
        return parseStatement_If(tokens)
    elif nextIsIdentifier(tokens):
        return parseStatement_Assignment(tokens)
    else:
        raise Exception("unknown statement type")

def parseStatement_Block(tokens, a = 0):
    statements = []
    acceptLetter(tokens, "{")
    while not nextIsLetter(tokens, "}"):
        statement = parseStatement(tokens)
        statements.append(statement)
    acceptLetter(tokens, "}")

    if len(statements) == 1:
        return statements[0]
    else:
        return ast.BlockStmtAST(statements)

def parseStatement_Return(tokens):
    acceptKeyword(tokens, "return")
    expression = parseExpression(tokens)
    acceptLetter(tokens, ";")
    return ast.ReturnStmtAST(expression)

def parseStatement_Let(tokens):
    acceptKeyword(tokens, "let")
    dataType = parseType(tokens)
    name = acceptIdentifier(tokens)
    acceptLetter(tokens, "=")
    expression = parseExpression(tokens)
    acceptLetter(tokens, ";")
    return ast.LetStmtAST(name, dataType, expression)

def parseStatement_Assignment(tokens):
    targetName = acceptIdentifier(tokens)
    if nextIsLetter(tokens, "["):
        acceptLetter(tokens, "[")
        offset = parseExpression(tokens)
        acceptLetter(tokens, "]")
        acceptLetter(tokens, "=")
        expression = parseExpression(tokens)
        acceptLetter(tokens, ";")
        return ast.ArrayAssignmentStmtAST(targetName, offset, expression)
    else:
        acceptLetter(tokens, "=")
        expression = parseExpression(tokens)
        acceptLetter(tokens, ";")
        return ast.AssignmentStmtAST(targetName, expression)

def parseStatement_While(tokens):
    acceptKeyword(tokens, "while")
    acceptLetter(tokens, "(")
    condition = parseExpression(tokens)
    acceptLetter(tokens, ")")
    statement = parseStatement(tokens)
    return ast.WhileStmtAST(condition, statement)

def parseStatement_If(tokens):
    acceptKeyword(tokens, "if")
    acceptLetter(tokens, "(")
    condition = parseExpression(tokens)
    acceptLetter(tokens, ")")
    thenStatement = parseStatement(tokens)
    if nextIsKeyword(tokens, "else"):
        acceptKeyword(tokens, "else")
        elseStatement = parseStatement(tokens)
        return ast.IfElseStmtAST(condition, thenStatement, elseStatement)
    else:
        return ast.IfStmtAST(condition, thenStatement)

def parseExpression(tokens):
    '''
    Expression parsing happens at different levels
    because of operator precedence rules.
    '''
    return parseExpression_ComparisonLevel(tokens)

def parseExpression_ComparisonLevel(tokens):
    expressionLeft = parseExpression_AddSubLevel(tokens)
    if nextIsComparisonOperator(tokens):
        operator = parseComparisonOperator(tokens)
        expressionRight = parseExpression_AddSubLevel(tokens)
        return ast.ComparisonExprAST(operator, expressionLeft, expressionRight)
    else:
        return expressionLeft

def parseComparisonOperator(tokens):
    if nextIsLetter(tokens, "="):
        acceptLetter(tokens, "=")
        acceptLetter(tokens, "=")
        return "=="
    elif nextIsLetter(tokens, "<"):
        acceptLetter(tokens, "<")
        if nextIsLetter(tokens, "="):
            acceptLetter(tokens, "=")
            return "<="
        else:
            return "<"
    elif nextIsLetter(tokens, ">"):
        acceptLetter(tokens, ">")
        if nextIsLetter(tokens, "="):
            acceptLetter(tokens, "=")
            return ">="
        else:
            return ">"
    elif nextIsLetter(tokens, "!"):
        acceptLetter(tokens, "!")
        acceptLetter(tokens, "=")
        return "!="

def parseExpression_AddSubLevel(tokens):
    terms = []

    term = parseExpression_MulDivLevel(tokens)
    terms.append(ast.AddedTerm(term))

    while nextIsOneOfLetters(tokens, "+", "-"):
        if nextIsLetter(tokens, "+"):
            acceptLetter(tokens, "+")
            term = parseExpression_MulDivLevel(tokens)
            terms.append(ast.AddedTerm(term))
        elif nextIsLetter(tokens, "-"):
            acceptLetter(tokens, "-")
            term = parseExpression_MulDivLevel(tokens)
            terms.append(ast.SubtractedTerm(term))

    if len(terms) == 1 and isinstance(terms[0], ast.AddedTerm):
        return terms[0].expr
    else:
        return ast.AddSubExprAST(terms)

def parseExpression_MulDivLevel(tokens):
    terms = []

    factor = parseExpression_FactorLevel(tokens)
    terms.append(ast.MultipliedTerm(factor))

    while nextIsOneOfLetters(tokens, "*", "/"):
        if nextIsLetter(tokens, "*"):
            acceptLetter(tokens, "*")
            factor = parseExpression_FactorLevel(tokens)
            terms.append(ast.MultipliedTerm(factor))
        elif nextIsLetter(tokens, "/"):
            acceptLetter(tokens, "/")
            factor = parseExpression_FactorLevel(tokens)
            terms.append(ast.DividedTerm(factor))
    
    if len(terms) == 1 and isinstance(terms[0], ast.MultipliedTerm):
        return terms[0].expr
    else:
        return ast.MulDivExprAST(terms)

def parseExpression_FactorLevel(tokens):
    if nextIsIdentifier(tokens):
        name = acceptIdentifier(tokens)
        return ast.VariableAST(name)
    elif nextIsInteger(tokens):
        value = acceptInteger(tokens)
        return ast.ConstIntAST(value)
    elif nextIsLetter(tokens, "("):
        acceptLetter(tokens, "(")
        expression = parseExpression(tokens)
        acceptLetter(tokens, ")")
        return expression
    elif nextIsLetter(tokens, "@"):
        return parseFunctionCall(tokens)

def parseFunctionCall(tokens):
    acceptLetter(tokens, "@")
    name = acceptIdentifier(tokens)
    arguments = parseCallArguments(tokens)
    return ast.FunctionCallAST(name, arguments)

def parseCallArguments(tokens):
    acceptLetter(tokens, "(")
    if nextIsLetter(tokens, ")"):
        return []
    else:
        arguments = []
        while True:
            expression = parseExpression(tokens)
            arguments.append(expression)
            if nextIsLetter(tokens, ","):
                acceptLetter(tokens, ",")
                continue
            else:
                break
        acceptLetter(tokens, ")")
        return arguments


def nextIsKeyword(tokens, keyword):
    if len(tokens) == 0: return False
    nextToken = tokens.peekNext()
    if isinstance(nextToken, IdentifierToken):
        return nextToken.value == keyword
    return False

def nextIsLetter(tokens, letter):
    if len(tokens) == 0: return False
    nextToken = tokens.peekNext()
    if isinstance(nextToken, SingleCharToken):
        return nextToken.value == letter
    return False

def nextIsOneOfLetters(tokens, *letters):
    return any(nextIsLetter(tokens, c) for c in letters)

def nextIsIdentifier(tokens):
    if len(tokens) == 0: return False
    return isinstance(tokens.peekNext(), IdentifierToken)

def nextIsInteger(tokens):
    if len(tokens) == 0: return False
    return isinstance(tokens.peekNext(), IntegerToken)

def nextIsComparisonOperator(tokens):
    return nextIsOneOfLetters(tokens, "<", ">", "=", "!")


def acceptKeyword(tokens, keyword):
    if nextIsKeyword(tokens, keyword):
        tokens.takeNext()
    else:
        raise Exception(f"expected keyword '{keyword}'")

def acceptLetter(tokens, letter):
    if nextIsLetter(tokens, letter):
        tokens.takeNext()
    else:
        raise Exception(f"expected token '{letter}'")

def acceptIdentifier(tokens):
    if nextIsIdentifier(tokens):
        return tokens.takeNext().value
    else:
        raise Exception("expected identifier")

def acceptInteger(tokens):
    if nextIsInteger(tokens):
        return tokens.takeNext().value
    else:
        raise Exception("expected integer")