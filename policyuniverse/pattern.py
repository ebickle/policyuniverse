import re
from policyuniverse.glob import intersect as glob_intersect
from policyuniverse.glob import Match

_VARIABLE_NAME_MATCH = re.compile("^[A-Za-z][A-Za-z0-9]*$").match

def pattern_to_regex(pattern, wildcard_exp="."):
    """
    Translates an AWS string pattern into a regular expression pattern.

    :param pattern: The AWS string pattern to translate into a regular expression pattern.
    :param wildcard_exp: The regular expression used to match a single wildcard character.
    :type pattern: str
    :type wildcard_exp: str
    :returns: A regular expression pattern.
    :rtype: str

    String patterns can contain:
        * \* - a sequence of multiple wildcard characters.
        * ? - a single wildcard character.
        * ${variable_name} - A named variable.
        * ${\*} - the literal character \*.
        * ${?} - the literal character ?.
        * ${$} - the literal character $.
    """
    exp = ""
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        i = i + 1

        if c == "*":
            exp += wildcard_exp + "*"
        elif c == "?":
            exp += wildcard_exp
        elif c == "$":
            if i >= n or pattern[i] != "{":
                raise ValueError("Curly bracket ({{) expected in pattern ({}).".format(i))

            end_idx = pattern.find("}", i + 1)
            if end_idx < 0:
                raise ValueError("Curly bracket (}}) expected in pattern ({}).".format(i + 1))

            variable_name = pattern[i + 1:end_idx]
            if len(variable_name) == 0:
                raise ValueError("Variable name expected in pattern ({}).".format(i + 1))            
            
            if variable_name == '*' or variable_name == '?' or variable_name == '$':
                exp += re.escape(variable_name)
            else:
                if not _VARIABLE_NAME_MATCH(variable_name):
                    raise ValueError("Variable name expected to only contain alphanumeric characters, starting with a letter ({}).".format(i + 1))
                exp += "(?P<" + variable_name + ">" + wildcard_exp + "*)"

            i = i + 2 + len(variable_name)                            
        else:
            exp += re.escape(c)
    return exp

def arn_pattern_to_regex(arn_pattern):    
    """
    Translates an ARN format into a regular expression pattern.
    :param arn_pattern: The ARN pattern to translate into a regular expression pattern.
    :type arn_pattern: str
    :returns: A regular expression pattern.
    :rtype: str
    """    
    if not arn_pattern.startswith("arn:"):
        raise ValueError("ARN pattern does not begin with 'arn:'.")

    arn_segments = arn_pattern.split(':', 5)
    if len(arn_segments) != 6:
        raise ValueError("Incorrect number of segments in ARN pattern.")

    exp = "^arn:"
    for segment in arn_segments[1:5]:
        exp += pattern_to_regex(segment, "[^:]") + ":"
    exp += pattern_to_regex(arn_segments[5]) + "$"

    return exp


def pattern_to_glob(pattern, variables_as_wildcards=True):
    """
    Translates an ARN pattern into a glob pattern.
    :param arn_pattern: The ARN pattern to translate into a glob pattern.
    :type arn_pattern: str
    :returns: A glob pattern.
    :rtype: str
    """    
    glob = ""
    groups = []

    for item in iterate_pattern(pattern):
        if item[0] == "$":
            if item == "${$}":
                glob += "$"
            elif item == "${*}":
                glob += "\\*"
            elif item == "${?}":
                glob += "\\?"
            elif variables_as_wildcards:
                groups.append(item)
                glob += "*"
            else:
                glob += item
        elif item == "\\":
            glob += "\\\\"
        else:
            if item == "*" or item == "?":
                groups.append(item)
            glob += item
    
    return (glob, groups)    

def match_arn_pattern(arn_pattern, resource):
    if resource == "*":
        resource = "arn:*:*:*:*:*"

    if not arn_pattern.startswith("arn:"):
        raise ValueError("ARN pattern does not begin with 'arn:'.")

    if not resource.startswith("arn:"):
        raise ValueError("Resource does not begin with 'arn:'.")

    arn_segments = arn_pattern.split(":", 5)
    if len(arn_segments) != 6:
        raise ValueError("Incorrect number of segments in ARN pattern.")

    resource_segments = resource.split(":", 5)
    if len(resource_segments) != 6:
        raise ValueError("Incorrect number of segments in resource.")

    matches = []
    for arn_segment, resource_segment in zip(arn_segments[1:], resource_segments[1:]):
        arn_glob, group_names = pattern_to_glob(arn_segment, True)
        resource_glob = pattern_to_glob(resource_segment, False)[0]
        match = glob_intersect(arn_glob, resource_glob)
        if match:
            matches.extend(list(zip(group_names, match.groups)))
        else:
            return None
    return Match(matches)

def iterate_pattern(pattern):    
    """
    Iterates over the components of an AWS string pattern, splitting at variables and wildcards.

    :param pattern: The AWS string pattern to iterate.
    :type pattern: str
    :returns: An iterator of the components of the specified pattern.
    """
    start_idx, cur_idx, n = 0, 0, len(pattern)
    while cur_idx < n:
        c = pattern[cur_idx]
        if c == "*" or c == "?" or c == "$":
            # Yield literal characters up until this point.
            if start_idx < cur_idx:
                yield pattern[start_idx:cur_idx]

            if c == "$":
                if cur_idx + 1 >= n or pattern[cur_idx + 1] != "{":
                    raise ValueError("Curly bracket ({{) expected ({}).".format(cur_idx))

                end_idx = pattern.find("}", cur_idx + 2)
                if end_idx < 0:
                    raise ValueError("Curly bracket (}}) expected ({}).".format(cur_idx + 2))

                if cur_idx + 2 >= end_idx:
                    raise ValueError("Variable name expected in pattern ({}).".format(cur_idx + 2))

                variable_name = pattern[cur_idx + 2:end_idx]
                if len(variable_name) == 0:
                    raise ValueError("Variable name expected in pattern ({}).".format(cur_idx + 1))            
                
                if variable_name != '*' and variable_name != '?' and variable_name != '$' and not _VARIABLE_NAME_MATCH(variable_name):
                    raise ValueError("Variable name expected to only contain alphanumeric characters, starting with a letter ({}).".format(cur_idx + 2))
            else:
                end_idx = cur_idx

            variable = pattern[cur_idx:end_idx + 1]
            yield variable

            cur_idx = end_idx
            start_idx = end_idx + 1

        cur_idx += 1

    # Yield literal characters up until the end.
    if start_idx < n:
        yield pattern[start_idx:n]
