'''
Created on 5/03/2013

@author: Nick Wareing
'''

import abc

class Classifications:
    (Positive, Negative) = range(2)


class CandidateEliminator(object):
    '''Implements an abstract form of the Candidate Elimination
    algorithm. The algorithm is formed in a general sense such that
    all of the language independent subroutines are broken out into
    abstract methods which need to be implemented by a child class.'''
    __metaclass__ = abc.ABCMeta


    def _runAlgorithm(self, trainingSet, quiet=False):
        '''Takes a training set and runs the candidate elimination
        algorithm to create a version space. It returns two vectors,
        S & G representing the most specific and most general hypothesis
        in the version space, respectively.'''

        G = self._initializeG()
        S = self._initializeS()

        count = 0  # Keep count of which example we are up to.
        for example in trainingSet:
            if self._isPositive(example):
                G = self._removeNonMatching(G, example[0])

                Snew = S[:]  # Create a clone of S before we work on it.
                for s in S:
                    if not self._match(s, example[0]):
                        Snew.remove(s)
                        generalization = self._getMinGeneralization(s, example[0])
                        if self._processGeneralization(generalization, G):
                            Snew.append(generalization)
                S = Snew[:]
                S = self._removeMoreGeneral(S)
            else:  # If the example is negative
                S = self._removeMatching(S, example[0])

                Gnew = G[:]  # Create a clone of G before we work on it.
                for g in G:
                    if self._match(g, example[0]):
                        Gnew.remove(g)
                    specializations = self._getMinSpecializations(g, example[0])
                    specializations = self._processSpecializations(specializations, S)
                    Gnew += specializations
                G = Gnew[:]

                G = self._removeMoreSpecific(G)

            if not quiet:
                print "Example: %d" % count
                print example
                print "G:"
                for g in G:
                    print g
                print "S:"
                for s in S:
                    print s
                print '------------------'

            if S == G:
                break  # The version space has converged, no need to continue.

            count += 1
        return G, S

    @abc.abstractmethod
    def _removeNonMatching(self, hypothesis, instance):
        '''Remove from G any hypotheses that do not match d.'''
        return

    @abc.abstractmethod
    def _removeMatching(self, hypothesis, instance):
        '''Remove from S any hypotheses that match d.'''
        return

    @abc.abstractmethod
    def _removeMoreGeneral(self, hypothesis):
        '''Remove from S any h that is more general
        than another hypothesis in S.'''
        return

    @abc.abstractmethod
    def _removeMoreSpecific(self, hypothesis):
        '''Remove from G any h this more specific
        than another hypothesis in G.'''
        return

    @abc.abstractmethod
    def _initializeS(self):
        '''Initialize S to the set of most-specific
        hypotheses in H.'''
        return

    @abc.abstractmethod
    def _initializeG(self):
        '''Initialize G to the set of most-general
        hypotheses in H.'''
        return

    @abc.abstractmethod
    def _isPositive(self, example):
        '''Returns True if the example is positive,
        otherwise False.'''
        return

    @abc.abstractmethod
    def _match(self, hyp, instance):
        '''Takes two hypothesis and returns true if they
        match (given any example concept) and False otherwise.'''
        return

    @abc.abstractmethod
    def _moreGeneral(self, hyp1, hyp2):
        '''Returns True if hyp2 satisfies more concepts than hyp1.'''
        return

    @abc.abstractmethod
    def _moreSpecific(self, hyp1, hyp2):
        return

    @abc.abstractmethod
    def _getMinGeneralization(self, s, instance):
        '''Generates all minimal generalizations, h, of
        s, such that h matches d.'''
        return

    @abc.abstractmethod
    def _getMinSpecializations(self, g, instance):
        '''Generates all minimal specializations, h, of
        g, such that h does not match d.'''
        return

    @abc.abstractmethod
    def _processSpecializations(self, specializations, S):
        '''Removes specializations for which there is no
        member of S more specific.'''
        return

    @abc.abstractmethod
    def _processGeneralization(self, generalization, G):
        '''Removes generalizations for which no member
        of G is more general.'''
        return

class Representation(CandidateEliminator):
    '''Implements the language specific subroutines
    and classification functions for the candidate
    elimination algorithm.'''

    def __init__(self, trainingSet):
        self.numFactors = len(trainingSet[0][0])
        self.G, self.S = self._runAlgorithm(trainingSet)


    def classify(self, example):
        '''Classifies unseen examples based on the obtained
        version space. Returns positive/negative when it is
        certain and performs voting when it is uncertain.
        
        >>> r.classify(('Y', 'N', 'N', 'Y', 'Y', 'Y', 'N', 'N', 'Y', 'Y'))
        (1, '5/65')
        >>> r.classify(('Y', 'Y', 'N', 'Y', 'Y', 'Y', 'N', 'N', 'Y', 'Y'))
        (1, None)
        >>> r.classify(('N', 'N', 'N', 'Y', 'N', 'Y', 'N', 'N', 'N', 'Y'))
        (0, None)
        >>> r.classify(('Y', 'N', 'N', 'Y', 'Y', 'Y', 'N', 'N', 'N', 'Y'))
        (1, '22/65')
        '''

        if self._match(self.S[0], example):
            return Classifications.Positive, None
        elif self._noGmatch(self.G, example):
            return Classifications.Negative, None
        else:
            sToG = self._enumerateVersionSpace(self.S, self.G)
            return self._performVoting(sToG, example)


    def _enumerateVersionSpace(self, S, G):
        '''Returns a list of all possible concepts in the version
        space ie. everything in S, everything in G, and everything in between.
        '''

        sToG = []
        sToG += S
        sToG += G
        sToG = set(sToG)
        s = S[0]

        for g in G:
            for i, factor in enumerate(g):
                if factor != s[i]:
                    newHypothesis = list(g)
                    newHypothesis[i] = s[i]
                    sToG.add(tuple(newHypothesis))
        return list(sToG)


    def _performVoting(self, sToG, example):
        '''Given an unseen example and the enumerated
        version space, this function counts the number
        of hypothesis in the expanded version space that
        the example matches. If >= half match, then the
        function votes positive, otherwise it votes negative.
        In both cases it returns a tuple of it's decision
        and the odds'''

        satisfiedCount = 0
        for hyp in sToG:
            if self._match(hyp, example):
                satisfiedCount += 1
        length = len(sToG)
        half = round(0.5 * length)
        if satisfiedCount >= half:
            return (Classifications.Positive,
                    str(satisfiedCount) + '/' + str(length))
        else:
            return (Classifications.Negative,
                    str(satisfiedCount) + '/' + str(length))


    def _noGmatch(self, G, example):
        '''Returns True if the example does NOT match
        any of the hypothesis in G, otherwise it returns False.'''

        for g in G:
            if self._match(g, example):
                return False
        return True


    def _runAlgorithm(self, trainingSet):
        '''Use the parent class (abstract) implementation of the
        candidate elimination algorithm.'''

        return super(Representation, self)._runAlgorithm(trainingSet)


    def _removeNonMatching(self, hypotheses, instance):
        '''Removes all the hypotheses that do not match
        the given instance.'''

        hypothesesNew = hypotheses[:]
        for g in hypotheses:
            if not self._match(g, instance):
                hypothesesNew.remove(g)
        return hypothesesNew[:]


    def _removeMatching(self, hypotheses, instance):
        '''Removes all the hypotheses that match the 
        given instance.'''

        hypothesesNew = hypotheses[:]
        for s in hypotheses:
            if self._match(s, instance):
                hypothesesNew.remove(s)
        return hypothesesNew[:]


    def _removeMoreGeneral(self, hypothesis):
        '''Included for completeness. Not required
        to don anything with the language chosen.'''

        return hypothesis


    def _removeMoreSpecific(self, hypothesis):
        '''Remove from G any h that is more specific
        than another hypothesis in G.'''

        hypothesisNew = hypothesis[:]
        for g1 in hypothesis:
            for g2 in hypothesis:
                if g1 != g2 and self._moreSpecific(g1, g2):
                    try:
                        hypothesisNew.remove(g1)
                        break
                    except ValueError:
                        continue
        return hypothesisNew[:]


    def _initializeS(self):
        '''
        >>> r._initializeS()
        [('0', '0', '0', '0', '0', '0', '0', '0', '0', '0')]
        '''

        return [tuple(['0' for factor in range(self.numFactors)])]


    def _initializeG(self):
        '''
        >>> r._initializeG()
        [('?', '?', '?', '?', '?', '?', '?', '?', '?', '?')]
        '''

        return [tuple(['?' for factor in range(self.numFactors)])]


    def _isPositive(self, example):
        '''Returns true if 'example' is positive,
        otherwise False
        
        >>> r._isPositive((('N', 'N', 'N', 'Y', 'N', 'N', 'N', 'Y', 'N', 'N'), '-'))
        False
        >>> r._isPositive((('N', 'N', 'N', 'Y', 'Y', 'Y', 'N', 'N', 'N', 'Y'), '+'))
        True
        '''

        if example[1] == '+':
            return True
        elif example[1] == '-':
            return False
        else:
            raise TypeError("Unexpected input")


    def _factorMatch(self, factor1, factor2):
        '''Returns a boolean indicating whether
        two factors logically _match
        
        >>> r._match('Y', 'N')
        False
        >>> r._match('N', 'Y')
        False
        >>> r._match('Y', '?')
        True
        >>> r._match('?', 'N')
        True
        >>> r._match('Y', 'Y')
        True
        '''

        match = True
        if factor1 != factor2:
            if factor1 != '?' and factor2 != '?':
                match = False
        return match


    def _match(self, hyp, instance):
        '''Return a boolean indicating whether
        the given hypothesis and instance are
        logical matches.

        >>> r._match(('big','?', '?'), ('small','red', 'circle'))
        False
        >>> r._match(('?','?', 'circle'), ('small','red', 'circle'))
        True
        >>> r._match(('?','?', '?'), ('small','red', 'circle'))
        True
        >>> r._match(('small','red', '?'), ('?','red', 'circle'))
        True
        '''

        for i, hypFactor in enumerate(hyp):
            insFactor = instance[i]
            if not self._factorMatch(hypFactor, insFactor):
                return False
        return True


    def _getFactorContradictions(self, tup1, tup2):
        '''Returns a list of index locations
        where factors are not logical equivalents
        
        >>> tup1 = ('N', 'N', 'N', 'Y', 'N', 'N', 'N', 'Y', 'N', 'Y')
        >>> tup2 = ('N', 'Y', 'N', 'N', 'N', 'N', 'Y', 'N', 'N', 'Y')
        >>> r._getFactorContradictions(tup1, tup2)
        [1, 3, 6, 7]
        '''

        contradictions = []
        for i, factor1 in enumerate(tup1):
            factor2 = tup2[i]
            if not self._factorMatch(factor1, factor2):
                contradictions.append(i)

        return contradictions


    def _moreGeneral(self, hyp1, hyp2):
        '''Returns True if hyp1 is more general
        than hyp2, otherwise it returns False.
        ie. every instance that satisfies hyp2
        also satisfies hyp1.
        
        >>> r._moreGeneral(('?', '?', '?'), ('Y', 'N', '?'))
        True
        >>> r._moreGeneral(('?', '?', '?'), ('Y', 'N', '?'))
        True
        >>> r._moreGeneral(('Y', 'N', '?'), ('Y', '?', '?'))
        False
        >>> r._moreGeneral(('Y', '?', '?'), ('?', 'N', '?'))
        False
        '''

        more = False
        if self._match(hyp1, hyp2):
            more = True
            for i, factor in enumerate(hyp2):
                if factor == '?' and hyp1[i] != '?':
                    more = False
        return more

    def _moreSpecific(self, hyp1, hyp2):
        '''Returns True if hyp1 is more specific
        than hyp2, otherwise it returns False.
        
        Achieved by calling the moreGeneral function with
        the arguments reversed.
        '''

        return self._moreGeneral(hyp2, hyp1)


    def _getMinGeneralization(self, s, instance):
        '''Returns the unique minimal generalization, h, of
        s such that h matches the given positive instance and
        some member of G is more general (or equally general?)
        than h.
        
        Implements the Find-S conjunctive hypotheses algorithm.
        Returns a tuple.

        >>> r._getMinGeneralization(('Y', 'N', 'Y'), ('N', 'N', 'Y'))
        ('?', 'N', 'Y')
        >>> r._getMinGeneralization(('0', '0', '0'), ('Y', 'N', 'Y'))
        ('Y', 'N', 'Y')
        '''

        contradictions = self._getFactorContradictions(s, instance)
        sList = list(s)
        for i in contradictions:
            if s[i] == '0':
                sList[i] = instance[i]
            else:
                sList[i] = '?'
        return tuple(sList)


    def _getMinSpecializations(self, g, instance):
        '''Specialize just enough.
        Returns a list of tuples.
        
        >>> g = ('?', '?', '?')
        >>> instance = ('Y', 'N', 'Y')
        >>> r._getMinSpecializations(g, instance)
        [('N', '?', '?'), ('?', 'Y', '?'), ('?', '?', 'N')]

        >>> g = ('N', '?', '?')
        >>> instance = ('N', 'Y', 'N')
        >>> r._getMinSpecializations(g, instance)
        [('N', 'N', '?'), ('N', '?', 'Y')]
        '''

        specializations = []

        for i, factor in enumerate(g):
            if factor == '?':
                gList = list(g)
                if instance[i] == 'Y':
                    gList[i] = 'N'
                else:
                    gList[i] = 'Y'
                specializations.append(tuple(gList))

        return specializations


    def _processSpecializations(self, specializations, S):
        '''
        >>> S = [('?', 'Y', 'N')]
        >>> specializations = [('Y', '?', 'N'), ('?', 'Y', 'N'), ('?', 'N', 'N')]
        >>> r._processSpecializations(specializations, S)
        [('?', 'Y', 'N')]

        >>> S = [('Y', 'Y', 'N')]
        >>> specializations = [('N', '?', '?'), ('Y', '?', '?'), ('?', 'N', '?'), ('?', '?', 'N') , ('?', '?', 'Y')]
        >>> r._processSpecializations(specializations, S)
        [('Y', '?', '?'), ('?', '?', 'N')]
        '''

        validSpecializations = []
        for s in S:
            for hyp in specializations:
                if self._moreGeneral(hyp, s):
                    validSpecializations.append(hyp)
                elif s == self._initializeS()[0]:
                    validSpecializations.append(hyp)
        return validSpecializations


    def _processGeneralization(self, generalization, G):
        '''
        >>> G = [('Y', '?', '?'), ('?', '?', 'N')]
        >>> r._processGeneralization(('?', 'N', 'N'), G)
        True

        >>> G = []
        >>> r._processGeneralization(('?', 'N', '?', '?', '?', 'Y', 'N', 'N', 'N', 'Y'), G)
        True

        >>> G = [('?', 'N', '?', '?', '?', 'Y', 'N', 'N', 'N', 'Y')]
        >>> r._processGeneralization(('?', 'N', '?', '?', '?', 'Y', '?', 'N', 'N', 'Y'), G)
        False
        '''

        if G == []:  # Handle the edge-case where G is empty.
            return True
        for g in G:
            if self._moreSpecific(generalization, g):
                return True
        return False


if __name__ == "__main__":
    import doctest
    from data_doctests import getSet
    data = getSet()
    representation = Representation(data[:60])
    doctest.testmod(extraglobs={'r': representation})
