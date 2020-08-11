import sys
import copy

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        w, h = draw.textsize(letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # do the deep copy of domains
        domain_copy = copy.deepcopy(self.domains)

        # iterate through domains copy
        for variable in domain_copy:
            # getting the variable length
            length = variable.length
            # iterate through words in domain
            for word in domain_copy[variable]:
                if len(word) != length:
                    # if length of the word doesn't fit variable, delete it from
                    # the original domain (not copy)
                    self.domains[variable].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # getting x and y ovelapping cells, unpack cords to variables
        xoverlap, yoverlap = self.crossword.overlaps[x, y]

        # make variable describing if revision was made
        revision_made = False

        # making domains copy
        domains_copy = copy.deepcopy(self.domains)

        # if overlap occurs
        if xoverlap:
            # iterate through words in x's domain
            for xword in domains_copy[x]:
                matched_value = False
                # iterate through words in y's domain
                for yword in self.domains[y]:
                    # if x's word and y's word have same letter in overlapping position
                    if xword[xoverlap] == yword[yoverlap]:
                        matched_value = True
                        break   # no need to check rest of y's words for that x
                if matched_value:
                    continue   # if x and y was matched, proceed with another x
                else:
                    self.domains[x].remove(xword) # no matching y's word to x, removing word from domain
                    revision_made = True

        # return bolean if revision was made
        return revision_made

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        if not arcs:
            # no arcs provided, start with an initial queue of all of the arcs in the problem
            queue = []
            # populating queue
            for variable1 in self.domains:
                for variable2 in self.crossword.neighbors(variable1):
                    if self.crossword.overlaps[variable1, variable2] is not None:
                        queue.append((variable1, variable2))

        while len(queue) > 0:
            x, y = queue.pop(0)
            if self.revise(x, y):
                if len(self.domains[x]) == 0:
                    return False
                for neighbour in self.crossword.neighbors(x):
                    if neighbour != y:
                        queue.append((neighbour, x))
            return True

    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        for variable in self.domains:
            if variable not in assignment:
                return False
        return True

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # all values are distinct, every value is the correct length,
        # and there are no conflicts between neighboring variables.

        # check if all values are distinct
        words = [*assignment.values()]
        if len(words) != len(set(words)):
            return False

        # check if every value is the correct length
        for variable in assignment:
            if variable.length != len(assignment[variable]):
                return False

        # check if there are any conflicts between neighbouring variables
        for variable in assignment:
            for neighbour in self.crossword.neighbors(variable):
                if neighbour in assignment:
                    x, y = self.crossword.overlaps[variable, neighbour]
                    if assignment[variable][x] != assignment[neighbour][y]:
                        return False

        # all cases checked, no conflicts, can return True
        return True

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        # make temporary dict for holding values
        word_dict = {}

        # getting neighbours of var
        neighbours = self.crossword.neighbors(var)

        # iterating through var's words
        for word in self.domains[var]:
            eliminated = 0
            for neighbour in neighbours:
                # don't count if neighbor has already assigned value
                if neighbour in assignment:
                    continue
                else:
                    # calculate overlap between two variables
                    xoverlap, yoverlap = self.crossword.overlaps[var, neighbour]
                    for neighbour_word in self.domains[neighbour]:
                        # iterate through neighbour's words, check for eliminate ones
                        if word[xoverlap] != neighbour_word[yoverlap]:
                            eliminated += 1
            # add eliminated neighbour's words to temporary dict
            word_dict[word] = eliminated

        # sort variables dictionary by number of eliminated neighbour values
        sorted_dict = {k: v for k, v in sorted(word_dict.items(), key=lambda item: item[1])}

        return [*sorted_dict]

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        choice_dict = {}

        # iterating through variables in domains
        for variable in self.domains:
            # iterating through variables in assignment
            if variable not in assignment:
                # if variable is not yet in assigment, add it to temp dict
                choice_dict[variable] = self.domains[variable]

        # make list of variables sorted by number of remaining values
        sorted_list = [v for v, k in sorted(choice_dict.items(), key=lambda item:len(item[1]))]

        # return variable with the minimum number of remaining values
        return sorted_list[0]

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # if assignment is already ready
        if len(assignment) == len(self.domains):
            return assignment

        # selecting one of unassigned variables
        variable = self.select_unassigned_variable(assignment)

        # iterating through words in that variable
        for value in self.domains[variable]:
            # making assignment copy, with updated variable value
            assignment_copy = assignment.copy()
            assignment_copy[variable] = value
            # checking for consistency, getting result of that new assignment backtrack
            if self.consistent(assignment_copy):
                result = self.backtrack(assignment_copy)
                if result is not None:
                    return result
        return None


def main():
    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
