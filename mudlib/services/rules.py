# TODO: Is it possible to make the inference more intelligent when
#       it comes to variable naming?  As it is, theres a lot of
#       reliance on the fact that the variables will be named the
#       same for the same argument througout the facts.

from mudlib import Service

class RulesService(Service):
    __sorrows__ = 'rules'

    def Run(self):
        pass # self.kb = KnowledgeBase()

    # Externally callable functionality.

    def Add(self):
        pass


class KnowledgeBase:
    def __init__(self):
        self.implications = []
        self.facts = []

        self.AddImplication("(american ?x) & (weapon ?y) & (nation ?z) & (hostile ?z) & (sells ?x ?z ?y) => (criminal ?x)")
        self.AddImplication("(owns Nono ?x) & (missile ?x) => (sells West Nono ?x)")
        self.AddImplication("(missile ?x) => (weapon ?x)")
        self.AddImplication("(enemy ?x America) => (hostile ?x)")

        self.ForwardChainString("(american West)")
        self.ForwardChainString("(nation Nono)")
        self.ForwardChainString("(enemy Nono America)")
        self.ForwardChainString("(owns Nono M1)")
        self.ForwardChainString("(missile M1)")

        print "* BackwardChain (criminal ?x)"
        matches = self.BackwardChainString("(criminal ?x)")
        print "* =", matches

    def AddImplication(self, s):
        self.implications.append(Implication(s))

    # -----------------------------------------------
    # BackwardChain
    # -----------------------------------------------

    def BackwardChainString(self, s):
        sentence = Sentence()
        sentence.SetString(s)
        return self.BackwardChain(sentence)

    def BackwardChain(self, question):
        return self.BackwardChainList([ question ], {})

    def BackwardChainList(self, questions, variables, depth=1):
        if len(questions) == 0:
            return [ variables ]

        answers = []
        q = questions[0]

        for fact in self.facts:
            localVariables = fact.Unify(q)
            if localVariables is not None:
                localVariables.update(variables)
                answers.append(localVariables)
                if depth == 1:
                    print " " * depth, "BackwardChainList:Fact", fact, localVariables

        for implication in self.implications:
            conclusion = implication.consequentList[0]
            localVariables = conclusion.Unify(q)
            if localVariables is not None:
                localVariables.update(variables)
                modifiedPremises = [ premise.Substitute(localVariables) for premise in implication.premiseList ]
                answers.extend(self.BackwardChainList(modifiedPremises, localVariables, depth=depth+1))
                print " " * depth, "BackwardChainList", conclusion, localVariables

        if len(questions) == 1:
            return answers

        ret = []
        remainingQuestions = questions[1:]
        for localVariables in answers:
            ret.extend(self.BackwardChainList(remainingQuestions, localVariables, depth=depth+1))
        return ret

    # -----------------------------------------------
    # ForwardChain
    # -----------------------------------------------

    def ForwardChain(self, newFact, internal=False):
        if internal:
            print "  ForwardChain", newFact
        else:
            print "* ForwardChain", newFact

        for fact in self.facts:
            if fact.IsRenaming(newFact):
                return

        self.facts.append(newFact)

        for implication in self.implications:
            for i in range(len(implication.premiseList)):
                sentence = implication.premiseList[i]
                unification = sentence.Unify(newFact)
                if unification is not None:
                    if len(implication.consequentList) != 1:
                        raise RuntimeError("KnowledgeBase.ForwardChain - Too many conclusions")
                    premises = implication.premiseList[:]
                    del premises[i]
                    conclusion = implication.consequentList[0]
                    self.FindAndInfer(premises, conclusion, unification)

    def FindAndInfer(self, premises, conclusion, unification1, depth=1):
        # print "*" * depth, "FindAndInfer", premises, conclusion, unification1
        if len(premises) == 0:
            self.ForwardChain(conclusion.Substitute(unification1), True)
        else:
            sentence = premises[0].Substitute(unification1)
            for fact in self.facts:
                unification2 = fact.Unify(sentence)
                if unification2 is not None:
                    unification2.update(unification1)
                    self.FindAndInfer(premises[1:], conclusion, unification2, depth+1)

    def ForwardChainString(self, s):
        sentence = Sentence()
        sentence.SetString(s)
        self.ForwardChain(sentence)



class Implication:
    def __init__(self, s):
        premise, consequent = s.split("=>")

        def ExtractSentences(s):
            l = []
            for bit in s.split("&"):
                sentence = Sentence()
                sentence.SetString(bit)
                l.append(sentence)
            return l

        self.premiseList = ExtractSentences(premise)
        self.consequentList = ExtractSentences(consequent)


class Sentence:
    predicate = None
    args = None

    def SetString(self, s):
        bits = s.strip().split(" ")
        if len(bits) < 2:
            raise RuntimeError("Bad sentence string", s)
        if bits[0][0] != "(":
            raise RuntimeError("Bad sentence start", s, bits)
        if bits[-1][-1] != ")":
            raise RuntimeError("Bad sentence end", s, bits)
        # Trim leading parenthesis.
        bits[0] = bits[0][1:]
        # Trim trailing parenthesis.
        bits[-1] = bits[-1][:-1]

        self.predicate = bits[0]
        self.args = bits[1:]

    def __str__(self):
        return "(%s %s)" % (self.predicate, str(self.args))

    def __repr__(self):
        return str(self)

    def Substitute(self, d):
        args = self.args[:]
        for i in range(len(args)):
            if d.has_key(args[i]):
                args[i] = d[args[i]]
        sentence = Sentence()
        sentence.predicate = self.predicate
        sentence.args = args
        return sentence

    def Unify(self, other):
        if self.predicate == other.predicate:
            d = {}
            for i in range(len(self.args)):
                argSelf = self.args[i]
                argOther = other.args[i]
                if argSelf.startswith("?"):
                    if argOther.startswith("?"):
                        continue
                    d[argSelf] = argOther
                elif argOther.startswith("?"):
                    d[argOther] = argSelf
                elif argSelf != argOther:
                    return
            return d

    def IsRenaming(self, other):
        if self.predicate == other.predicate:
            for i in range(len(self.args)):
                argSelf = self.args[i]
                argOther = other.args[i]
                if argSelf.startswith("?") and not argOther.startswith("?"):
                    return False
                elif argSelf != argOther:
                    return False
            return True
        return False
