def intersect(pattern1, pattern2, start1=0, start2=0):
    """
    Determines whether two glob patterns intersect.
    :param pattern1: The first glob pattern to compare.
    :param pattern2: The second glob pattern to compare.
    :param start1: The string index in pattern1 to begin comparing.
    :param start2: The string index in pattern2 to begin comparing.
    :type pattern1: str
    :type pattern2: str
    :type start1: int
    :type start2: int
    :returns: A Match object with the matching wildcard values from pattern1 if the patterns intersect; otherwise, None.
    """
    idx1, len1 = start1, len(pattern1)
    idx2, len2 = start2, len(pattern2)

    matched_groups = []

    while idx1 < len1 or idx2 < len2:
        # Skip over adjacent Kleene stars.
        while idx1 + 1 < len1 and pattern1[idx1] == "*" and pattern1[idx1 + 1] == "*":
            matched_groups.append(("*", ""))
            idx1 += 1
        while idx2 + 1 < len2 and pattern2[idx2] == "*" and pattern2[idx2 + 1] == "*":
            idx2 += 1

        # Kleene star in pattern1.
        if idx1 < len1 and pattern1[idx1] == "*":
            # If the final character is a star, the remainder of the other string matches.
            if idx1 + 1 == len1:
                matched_groups.append(("*", pattern2[idx2:]))
                return Match(matched_groups)

            idx2_kleene_start = idx2
            while idx2 < len2:
                match = intersect(pattern1, pattern2, idx1 + 1, idx2)
                if match:
                    idx2_kleene_end = idx2 + 1 if pattern2[idx2] == '*' else idx2
                    matched_groups.append(("*", pattern2[idx2_kleene_start:idx2_kleene_end]))
                    matched_groups += match.grouplist
                    return Match(matched_groups)
                idx2 += 1

        # Kleene star in pattern2.
        if idx2 < len2 and pattern2[idx2] == "*":
            # If the final character is a star, the remainder of the other string matches.
            if idx2 + 1 == len2:
                # Add all skipped stars in pattern1 as wildcard matches.
                for c in (pattern1[i] for i in range(idx1, len1) if pattern1[i] == '*'):
                    matched_groups.append(("*", "*"))
                return Match(matched_groups)
                            
            while idx1 < len1:
                match = intersect(pattern1, pattern2, idx1, idx2 + 1)
                if match:
                    # If we matched on a double Kleene star, add the star back to the results.
                    if pattern1[idx1] == '*' and pattern2[idx2] == '*' and len(match.grouplist) > 0:
                        matched_groups.append((match.grouplist[0][0], "*" + match.grouplist[0][1]))
                        matched_groups += match.grouplist[1:]
                    else:
                        matched_groups += match.grouplist
                    return Match(matched_groups)

                # Add all skipped stars in pattern1 as wildcard matches.
                if pattern1[idx1] == '*':
                    matched_groups.append(("*", "*"))

                idx1 += 1            

        # Determine whether there is anything to compare to.
        if idx1 >= len1 or idx2 >= len2:
            return None

        char1 = pattern1[idx1]
        char2 = pattern2[idx2]

        # Escaped character handling.
        if char1 == "\\":
            idx1 += 1
            if idx1 >= len1:
                raise ValueError("Character expected after backslash ({}).".format(idx1))
            if pattern1[idx1] in ["?", "*"]:
                char1 += pattern1[idx1]
            else:
                char1 = pattern1[idx1]
        if char2 == "\\":
            idx2 += 1
            if idx2 >= len2:
                raise ValueError("Character expected after backslash ({}).".format(idx2))
            if pattern2[idx2] in ["?", "*"]:
                char2 += pattern2[idx2]
            else:
                char2 = pattern2[idx2]

        # Match individual characters (non-Kleene star).
        if char1 == "?":
            matched_groups.append(("?", char2))
        elif char2 != "?" and char1 != char2:
            return None

        idx1 += 1
        idx2 += 1

    # All characters matched and we didn't end with a Kleene star.
    return Match(matched_groups)

class Match(object):
    def __init__(self, grouplist):
        self.grouplist = grouplist
    
    def __nonzero__(self):
        return True

    def __getitem__(self, i):
        return self.grouplist[i][1]

    @property
    def groups(self):
        return tuple([g[1] for g in self.grouplist])

    @property
    def groupdict(self):
        return dict([i for i in self.grouplist if i[0] != "*" and i[0] != "?"])
