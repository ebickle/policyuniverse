import unittest
from policyuniverse.glob import intersect
from policyuniverse.glob import Match

class TestIntersect(unittest.TestCase):
    def test_intersect_match(self):
        tests = [
            ("", "", []),
            ("*", "", [("*", "")]),
            ("", "*", []),
            ("?", "?", [("?", "?")]),
            ("?", "a", [("?", "a")]),
            ("a", "?", []),
            ("?b?", "abc", [("?", "a"), ("?", "c")]),
            ("abc", "?b?", []),
            ("a?c", "abc", [("?", "b")]),
            ("abc", "a?c", []),
            ("*", "literal", [("*", "literal")]),
            ("literal", "*", []),
            ("prefix*", "prefixliteral", [("*", "literal")]),
            ("prefixliteral", "prefix*", []),
            ("*suffix", "literalsuffix", [("*", "literal")]),
            ("literalsuffix", "*suffix", []),
            ("*", "*", [("*", "*")]),
            ("prefix*", "*", [("*", "*")]),
            ("*", "prefix*", [("*", "prefix*")]),
            ("*suffix", "*", [("*", "*")]),
            ("*", "*suffix", [("*", "*suffix")]),
            ("prefix*", "prefixliteral*", [("*", "literal*")]),
            ("prefixliteral*", "prefix*", [("*", "*")]),
            ("*suffix", "*literalsuffix", [("*", "*literal")]),
            ("*literalsuffix", "*suffix", [("*", "*")]),
            ("*suffix", "*literalsufsuffix", [("*", "*literalsuf")]),
            ("*literalsufsuffix", "*suffix", [("*", "*")]),
            ("prefix*suffix", "prefix*literal*suffix", [("*", "*literal*")]),
            ("prefix*literal*suffix", "prefix*suffix", [("*", "*"), ("*", "*")]),
            ("a*b*c", "a*b*d*b*c", [("*", "*"), ("*", "*d*b*")]),
            ("a*b*d*b*c", "a*b*c", [("*", "*"), ("*", "*"), ("*", "*"), ("*", "*")]),
            ("abc*", "*cde", [("*", "de")]),
            ("*cde", "abc*", [("*", "ab")]),
            ("?*b*?", "cbc", [("?", "c"), ("*", ""), ("*", ""), ("?", "c")]),
            ("cbc", "?*b*?", []),
            ("?*b*?", "acbca", [("?", "a"), ("*", "c"), ("*", "c"), ("?", "a")]),
            ("acbca", "?*b*?", []),
            ("*?*", "a", [("*", ""), ("?", "a"), ("*", "")]),
            ("a", "*?*", []),
            ("stream/*", "*", [("*", "*")]),
            ("*ba", "*b*", [("*", "*")])
        ]
        for a, b, c in tests:
            match = intersect(a, b)
            self.assertTrue(match)
            if match.grouplist != c:
                self.assertEqual(match.grouplist, c)

    def test_intersect_nonmatch(self):
        tests = [
            ("one", "two"),
            ("one", "oneone"),
            ("oneone", "one"),
            ("prefix*", "literal"),
            ("literal", "prefix*"),
            ("*suffix", "literal"),
            ("literal", "*suffix"),
            ("*two*", "onethree"),
            ("onethree", "*two*"),
            ("*a*b*c*d*", "a1b23d4"),            
            ("a1b23d4", "*a*b*c*d*"),            
            ("prefix*", "literalprefix*"),
            ("literalprefix*", "prefix*"),
            ("*suffix", "*suffixliteral"),
            ("*suffixliteral", "*suffix"),
            ("one*three", "three*two*one"),
            ("three*two*one", "one*three"),
            ("?*b*?", "bcb"),
            ("bcb", "?*b*?"),
            ("?", ""),
            ("" ,"?")
        ]
        for a, b in tests:
            match = intersect(a, b)
            self.assertFalse(match)

    def test_intersect_escaped_match(self):
        tests = [
            ("\\\\", "?"),
            ("\\\\", "*"),
            ("\\\\a", "??"),
            ("\\\\a", "*"),
            ("\\?", "?"),
            ("\\*", "?"),
            ("?", "\\*"),
            ("?", "\\?"),
            ("*", "\\*"),
            ("*", "\\?"),            
            ("\\*", "*"),
            ("\\?", "*"),
            ("\\?", "\\?"),
            ("\\*", "\\*"),
            ("\\a", "a"),
            ("a", "\\a")
        ]
        for a, b in tests:
            match = intersect(a, b)
            self.assertTrue(match)        

    def test_intersect_escaped_nomatch(self):
        tests = [
            ("\\?", "?a"),
            ("\\?", "a"),
            ("\\*", "?a"),
            ("\\*", "a"),
            ("\\*", ""),
            ("\\\\", "??")
        ]
        for a, b in tests:
            match = intersect(a, b)
            self.assertFalse(match)

    def test_intersect_escaped_valueerror(self):        
        with self.assertRaises(ValueError):
            intersect("\\", "a")

    def test_intersect_match_groups(self):
        match = intersect("?*b*?", "acbca")
        self.assertEqual(match.groups, ("a", "c", "c", "a"))

        match = intersect("abcd", "abcd")
        self.assertEqual(match.groups, ())

    def test_intersect_match_getitem(self):
        match = intersect("?*b*?", "acbca")
        self.assertEqual(match[1], "c")

    def test_intersect_match_getitem_indexerror(self):
        match = intersect("?", "a")
        with self.assertRaises(IndexError):        
            match[5]

class TestMatch(unittest.TestCase):
    def test_init(self):
        grouplist = [("a", "b")]
        match = Match(grouplist)
        self.assertEqual(match.grouplist, grouplist)

    def test_truthy(self):
        match = Match([])
        self.assertTrue(match)

    def test_getitem(self):
        grouplist = [("a", "b")]
        match = Match(grouplist)
        self.assertEqual(match[0], "b")        

    def test_getitem_indexerror(self):
        grouplist = [("a", "b")]
        match = Match(grouplist)
        with self.assertRaises(IndexError):        
            match[1]

    def test_groups(self):
        grouplist = [("a", "b"), ("c", "d")]
        match = Match(grouplist)
        self.assertEqual(match.groups, ("b", "d"))

    def test_groupdict(self):
        grouplist = [("a", "b"), ("*", "z"), ("c", "d"), ("a", "y")]
        match = Match(grouplist)
        self.assertEqual(match.groupdict, {"a":"y", "c":"d"})
