import unittest
from policyuniverse.pattern import pattern_to_regex
from policyuniverse.pattern import arn_pattern_to_regex
from policyuniverse.pattern import pattern_to_glob
from policyuniverse.pattern import match_arn_pattern
from policyuniverse.pattern import iterate_pattern

class TestPatternToRegex(unittest.TestCase):
    def test_pattern_to_regex_empty_pattern(self):
        result = pattern_to_regex("")
        self.assertEqual(result, "")
    
    def test_pattern_to_regex_invalid_start_bracket(self):
        with self.assertRaises(ValueError):
            pattern_to_regex("$ {value}")
        with self.assertRaises(ValueError):
            pattern_to_regex("$}{")

    def test_pattern_to_regex_invalid_end_bracket(self):
        with self.assertRaises(ValueError):        
            pattern_to_regex("${value")
        with self.assertRaises(ValueError):        
            pattern_to_regex("$")
        with self.assertRaises(ValueError):        
            pattern_to_regex("}${")

    def test_pattern_to_regex_varaible_empty_name(self):
        with self.assertRaises(ValueError):
            pattern_to_regex("${}")        

    def test_pattern_to_regex_varaible_invalid_name(self):
        with self.assertRaises(ValueError):
            pattern_to_regex("${ }")
        with self.assertRaises(ValueError):
            pattern_to_regex("${1A}")
        with self.assertRaises(ValueError):
            pattern_to_regex("${!}")

    def test_pattern_to_regex_escaped_literals(self):
        result = pattern_to_regex("${*}")
        self.assertEquals(result, "\*")
        result = pattern_to_regex("${?}")
        self.assertEquals(result, "\?")
        result = pattern_to_regex("${$}")
        self.assertEquals(result, "\$")

    def test_pattern_to_regex_literals(self):
        result = pattern_to_regex(".+-")
        self.assertEquals(result, "\.\+\-")

    def test_pattern_to_regex_wildcard_multiple(self):
        result = pattern_to_regex("*")
        self.assertEquals(result, ".*")
        result = pattern_to_regex("*", "^:")
        self.assertEquals(result, "^:*")        

    def test_pattern_to_regex_wildcard_single(self):
        result = pattern_to_regex("?")
        self.assertEquals(result, ".")    
        result = pattern_to_regex("?", "^:")
        self.assertEquals(result, "^:")            

    def test_pattern_to_regex_variable(self):
        result = pattern_to_regex("${variablename}")
        self.assertEquals(result, "(?P<variablename>.*)")
        result = pattern_to_regex("${variablename}", "^:")
        self.assertEquals(result, "(?P<variablename>^:*)")        

class TestArnPatternToRegex(unittest.TestCase):
    def test_arn_pattern_to_regex_invalid_arn_prefix(self):
        with self.assertRaises(ValueError):
            arn_pattern_to_regex(" arn:")
        with self.assertRaises(ValueError):
            arn_pattern_to_regex("arn")
        with self.assertRaises(ValueError):
            arn_pattern_to_regex("")

    def test_arn_pattern_to_regex_minimum_segments(self):
        with self.assertRaises(ValueError):
            arn_pattern_to_regex("arn:")
        with self.assertRaises(ValueError):            
            arn_pattern_to_regex("arn::::")        
        result = arn_pattern_to_regex("arn:::::")
        self.assertEquals(result, "^arn:::::$")

    def test_arn_pattern_to_regex_constant(self):
        result = arn_pattern_to_regex("arn:aws:appsync:us-west-2:123456789012:apis/AppSyncEndpointName/types/Query/fields/my-subscription")
        self.assertEquals(result, "^arn:aws:appsync:us\-west\-2:123456789012:apis/AppSyncEndpointName/types/Query/fields/my\-subscription$")
        result = arn_pattern_to_regex("arn:aws:s3:::my_corporate_bucket/exampleobject.png")
        self.assertEquals(result, "^arn:aws:s3:::my_corporate_bucket/exampleobject\.png$")

    def test_arn_pattern_to_regex_wildcards(self):
        result = arn_pattern_to_regex("arn:aws-*:s?:*:*:*/*")
        self.assertEquals(result, "^arn:aws\-[^:]*:s[^:]:[^:]*:[^:]*:.*/.*$")

class TestPatternToGlob(unittest.TestCase):
    def test_pattern_to_glob_blank(self):
        result = pattern_to_glob("")
        self.assertEquals(result, ("", []))

    def test_pattern_to_glob_escaped_dollarsign(self):
        result = pattern_to_glob("${$}")
        self.assertEquals(result, ("$", []))

    def test_pattern_to_glob_escaped_star(self):
        result = pattern_to_glob("${*}")
        self.assertEquals(result, ("\\*", []))

    def test_pattern_to_glob_escaped_questionmark(self):
        result = pattern_to_glob("${?}")
        self.assertEquals(result, ("\\?", []))

    def test_pattern_to_glob_escaped_backslash(self):
        result = pattern_to_glob("\\")
        self.assertEquals(result, ("\\\\", []))

    def test_pattern_to_glob_wildcard_multiple(self):
        result = pattern_to_glob("a*a")
        self.assertEquals(result, ("a*a", ["*"]))

    def test_pattern_to_glob_wildcard_single(self):
        result = pattern_to_glob("a?a")
        self.assertEquals(result, ("a?a", ["?"]))

    def test_pattern_to_glob_variable_as_wildcard(self):
        result = pattern_to_glob("a${VariableName}a")
        self.assertEquals(result, ("a*a", ["${VariableName}"]))

    def test_pattern_to_glob_variable_as_literal(self):
        result = pattern_to_glob("a${VariableName}a", False)
        self.assertEquals(result, ("a${VariableName}a", []))

class TestMatchArnPattern(unittest.TestCase):
    def test_match_arn_pattern_invalid_arn_pattern_valueerror(self):
        with self.assertRaises(ValueError):
            match_arn_pattern("a1:b2:c3:d4:e5:f6", "arn:aws:appsync:us-west-2:123123123:bucket_name")
        with self.assertRaises(ValueError):
            match_arn_pattern("arn:", "arn:aws:appsync:us-west-2:123123123:bucket_name")

    def test_match_arn_pattern_invalid_resource_valueerror(self):
        with self.assertRaises(ValueError):
            match_arn_pattern("arn:aws:appsync:us-west-2:123123123:bucket_name", "a1:b2:c3:d4:e5:f6")
        with self.assertRaises(ValueError):
            match_arn_pattern("arn:aws:appsync:us-west-2:123123123:bucket_name", "arn:")            

    def test_match_arn_pattern_full_wildcard_match(self):
        match = match_arn_pattern("arn:${Partition}:s3:${Region}:${Account}:${Bucket}", "*")            
        self.assertTrue(match)
        self.assertEqual(match.grouplist, [("${Partition}", "*"), ("${Region}", "*"), ("${Account}", "*"), ("${Bucket}", "*")])

    def test_match_arn_pattern_partial_wildcard_match(self):
        match = match_arn_pattern("arn:${Partition}:s3:${Region}:${Account}:${Bucket}", "arn:aws:s*:::bucket_name")            
        self.assertTrue(match)
        self.assertEqual(match.grouplist, [("${Partition}", "aws"), ("${Region}", ""), ("${Account}", ""), ("${Bucket}", "bucket_name")])

    def test_match_arn_pattern_literal_match(self):
        tests = [
            ("arn:${Partition}:s3:${Region}:${Account}:${Bucket}/${Object}", "arn:aws:s3:us-east-1:123123123:bucket_name/resource_name", [("${Partition}", "aws"), ("${Region}", "us-east-1"), ("${Account}", "123123123"), ("${Bucket}", "bucket_name"), ("${Object}", "resource_name")]),
            ("arn:*:kms:*:*:key/*", "arn:aws:kms:*:693621191777:key/*", [("*", "aws"), ("*", "*"), ("*", "693621191777"), ("*", "*")]),
            ("arn:${Partition}:kinesis:${Region}:${Account}:stream/${StreamName}", "arn:aws:kinesis:us-east-1:693621191777:*", [("${Partition}", "aws"), ("${Region}", "us-east-1"), ("${Account}", "693621191777"), ("${StreamName}", "*")])
        ]
        for a, b, c in tests:
            match = match_arn_pattern(a, b)
            self.assertTrue(match)
            self.assertEqual(match.grouplist, c)

    def test_match_arn_pattern_partial_wildcard_nonmatch(self):
        match = match_arn_pattern("arn:${Partition}:s3:${Region}:${Account}:${Bucket}/${Object}", "arn:aws:s3?:us-east-1:123123123:bucket_name")
        self.assertFalse(match)

    def test_match_arn_pattern_literal_nonmatch(self):
        tests = [
            ("arn:${Partition}:s3:${Region}:${Account}:${Bucket}/${Object}", "arn:aws:s3:us-east-1:123123123:bucket_name")
        ]
        for a, b in tests:
            match = match_arn_pattern(a, b)
            self.assertFalse(match)

class TestIteratePattern(unittest.TestCase):
    def test_iterate_pattern_empty_pattern(self):
        result = list(iterate_pattern(""))
        self.assertEqual(result, [])
    
    def test_iterate_pattern_literal(self):
        result = list(iterate_pattern(" "))
        self.assertEqual(result, [" "])
        result = list(iterate_pattern("1234-56 78.90"))
        self.assertEqual(result, ["1234-56 78.90"])

    def test_iterate_pattern_start_bracket(self):
        with self.assertRaises(ValueError):
            list(iterate_pattern("$ {value}"))
        with self.assertRaises(ValueError):            
            list(iterate_pattern("$}{"))

    def test_iterate_pattern_end_bracket(self):
        with self.assertRaises(ValueError):
            list(iterate_pattern("${value"))
        with self.assertRaises(ValueError):            
            list(iterate_pattern("$"))
        with self.assertRaises(ValueError):
            list(iterate_pattern("}${"))

    def test_iterate_pattern_varaible_empty_name(self):
        with self.assertRaises(ValueError):
            list(iterate_pattern("${}"))

    def test_iterate_pattern_varaible_invalid_name(self):
        with self.assertRaises(ValueError):
            list(iterate_pattern("${ }"))
        with self.assertRaises(ValueError):            
            list(iterate_pattern("${1A}"))
        with self.assertRaises(ValueError):
            list(iterate_pattern("${!}"))

    def test_iterate_pattern_wildcards(self):
        results = list(iterate_pattern("one*?${var}*${s} two "))
        self.assertEquals(results, ["one", "*", "?", "${var}", "*", "${s}", " two "])
        results = list(iterate_pattern("**?${var}middle*?"))
        self.assertEquals(results, ["*", "*", "?", "${var}", "middle", "*", "?"])        

    def test_iterate_pattern_escaped_literals(self):
        results = list(iterate_pattern("${?}${*}${$}"))
        self.assertEquals(results, ["${?}", "${*}", "${$}"])
