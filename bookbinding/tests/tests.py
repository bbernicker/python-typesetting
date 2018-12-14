
from bookbinding.skeleton import Column, Line2 as Line, Page2 as Page

def new_page():
    return Page(10, 34)

def next_column(column):
    page = new_page()
    id = column.id + 1 if column else 1
    return Column(page, id, 10, 34)

def next_line(line, height, leading):
    if line:
        column = line.column
        y = line.y + height + leading
        if y <= column.height:
            return Line(line, column, y, [])
    else:
        column = None
    return Line(line, next_column(column), height, [])

def test_line_positions():
    l1 = next_line(None, 10, 2)
    l2 = next_line(l1, 10, 2)
    l3 = next_line(l2, 10, 2)
    l4 = next_line(l3, 10, 2)

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    assert l1 == Line(None, c1, 10, [])
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c1, 34, [])
    assert l4 == Line(l3, c2, 10, [])

def make_paragraph(line, next_line, height, leading, n):
    for i in range(n):
        line = next_line(line, height, leading)
    return line

def unroll(start_line, end_line):
    lines = [end_line]
    while end_line is not start_line:
        end_line = end_line.previous
        lines.append(end_line)
    lines.reverse()
    return lines

def avoid_widows_and_orphans(line, next_line, add_paragraph, *args):
    end_line = add_paragraph(line, next_line, *args)
    lines = unroll(line, end_line)

    # Single-line paragraphs produce neither widows nor orphans.
    if len(lines) == 2:
        return end_line

    original_end_line = end_line

    def reflow():
        nonlocal end_line, lines
        end_line = add_paragraph(line, fancy_next_line, *args)
        lines = unroll(line, end_line)

    def is_orphan():
        return lines[1].column is not lines[2].column

    def fix_orphan():
        skips.add((lines[1].column.id, lines[1].y))
        reflow()

    def is_widow():
        return lines[-2].column is not lines[-1].column

    def fix_widow():
        nonlocal end_line, lines
        skips.add((lines[-2].column.id, lines[-2].y))
        reflow()

    def fancy_next_line(line, height, leading):
        line2 = next_line(line, height, leading)
        while (line2.column.id, line2.y) in skips:
            line2 = next_line(line, height, leading + 99999)
        return line2

    skips = set()

    if is_orphan():
        fix_orphan()
        if is_widow():
            fix_widow()
    elif is_widow():
        fix_widow()
        if is_orphan():
            fix_orphan()

    if is_orphan() or is_widow():
        return original_end_line

    return end_line

def test_nice_paragraph():
    # It produces neither an orphan nor a widow.
    l1 = next_line(None, 10, 2)
    l3 = avoid_widows_and_orphans(l1, next_line, make_paragraph, 10, 2, 2)
    l2 = l3.previous

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    assert l1 == Line(None, c1, 10, [])
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c1, 34, [])

def test_orphan():
    # A simple situation: an orphan that can be avoided by not using the
    # final line of the starting column.

    l1 = next_line(None, 10, 2)
    l2 = next_line(l1, 10, 2)

    l5 = avoid_widows_and_orphans(l2, next_line, make_paragraph, 10, 2, 3)
    l2, l3, l4 = unroll(l2, l5.previous)

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c2, 10, [])
    assert l4 == Line(l3, c2, 22, [])
    assert l5 == Line(l4, c2, 34, [])

def test_widow():
    # Another simple situation: a widow that can be avoided by not using
    # the final line of the starting column.
    l1 = None

    l5 = avoid_widows_and_orphans(l1, next_line, make_paragraph, 10, 2, 4)
    l1, l2, l3, l4 = unroll(l1, l5.previous)

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    assert l2 == Line(l1, c1, 10, [])
    assert l3 == Line(l2, c1, 22, [])
    assert l4 == Line(l3, c2, 10, [])
    assert l5 == Line(l4, c2, 22, [])

def test_widow_after_full_page():
    # A widow that can be avoided by not using the final line of the
    # second column of a 3-column paragraph.
    l0 = None

    l7 = avoid_widows_and_orphans(l0, next_line, make_paragraph, 10, 2, 7)
    l0, l1, l2, l3, l4, l5, l6 = unroll(l0, l7.previous)

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    c3 = Column(p, 3, 10, 34)
    assert l1 == Line(l0, c1, 10, [])
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c1, 34, [])
    assert l4 == Line(l3, c2, 10, [])
    assert l5 == Line(l4, c2, 22, [])
    assert l6 == Line(l5, c3, 10, [])
    assert l7 == Line(l6, c3, 22, [])

def test_orphan_plus_widow():
    # A two-line paragraph straddling the end of a column, that has both
    # an orphan and a widow but only needs a 1-line bump to fix both.
    l1 = next_line(None, 10, 2)
    l2 = next_line(l1, 10, 2)

    l4 = avoid_widows_and_orphans(l2, next_line, make_paragraph, 10, 2, 2)
    l3 = l4.previous

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c2, 10, [])
    assert l4 == Line(l3, c2, 22, [])

def test_orphan_then_full_page_then_widow():
    # A 3-column paragraph offering both an orphan and a window, that
    # needs a 1-line bump to fix both (and become a 2-column paragraph).
    l1 = next_line(None, 10, 2)
    l2 = next_line(l1, 10, 2)

    l7 = avoid_widows_and_orphans(l2, next_line, make_paragraph, 10, 2, 5)
    l2, l3, l4, l5, l6 = unroll(l2, l7.previous)

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    c3 = Column(p, 3, 10, 34)
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c2, 10, [])
    assert l4 == Line(l3, c2, 22, [])
    assert l5 == Line(l4, c2, 34, [])
    assert l6 == Line(l5, c3, 10, [])
    assert l7 == Line(l6, c3, 22, [])

def test_widow_whose_fix_creates_orphan():
    # Situation that needs two rounds: a widow that can be fixed by
    # bumping one line from the column, that then creates an orphan
    # requiring a second line to be bumped.
    l1 = next_line(None, 10, 2)

    l4 = avoid_widows_and_orphans(l1, next_line, make_paragraph, 10, 2, 3)
    l1, l2, l3 = unroll(l1, l4.previous)

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    assert l1 == Line(None, c1, 10, [])
    assert l2 == Line(l1, c2, 10, [])
    assert l3 == Line(l2, c2, 22, [])
    assert l4 == Line(l3, c2, 34, [])

def test_orphan_whose_fix_creates_widow():
    # Another situation that needs two rounds: an orphan that can be
    # fixed by bumping the final line to the next column, that then
    # creates a widow.
    l1 = next_line(None, 10, 2)
    l2 = next_line(l1, 10, 2)

    l6 = avoid_widows_and_orphans(l2, next_line, make_paragraph, 10, 2, 4)
    l2, l3, l4, l5 = unroll(l2, l6.previous)

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    c3 = Column(p, 3, 10, 34)
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c2, 10, [])
    assert l4 == Line(l3, c2, 22, [])
    assert l5 == Line(l4, c3, 10, [])
    assert l6 == Line(l5, c3, 22, [])

def test_widow_that_cannot_be_fixed():
    # What if the next page's columns are narrower, so trying to push
    # one line to the next page in fact fills the page and creates a
    # widow all over again?  Then the algorithm should give up and
    # return the original paragraph.

    state = 0
    def stateful_make_paragraph(line, next_line, height, leading):
        nonlocal state
        n = 6 if state else 4
        state = 1
        return make_paragraph(line, next_line, height, leading, n)

    l4 = avoid_widows_and_orphans(None, next_line,
                                  stateful_make_paragraph, 10, 2)
    l0, l1, l2, l3 = unroll(None, l4.previous)

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    assert l1 == Line(None, c1, 10, [])
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c1, 34, [])
    assert l4 == Line(l3, c2, 10, [])



def make_paragraph2(actions, a, line, next_line, height, leading, n):
    for i in range(n):
        line = next_line(line, height, leading)
    return a + 1, line

def section_title(actions, a, line, next_line, title):
    print(actions, a, title)
    line2 = next_line(line, 10, 2)
    if a + 1 == len(actions):
        return a + 1, line2
    #return a + 1, line2
    next_action, *args = actions[a + 1]
    a2, line3 = next_action(actions, a + 1, line2, next_line, *args)
    lines = unroll(line2, line3)

    # If we are in the same column as the following content, declare
    # victory.
    if lines[0].column is lines[1].column:
        return a2, line3

    # Try moving this title to the top of the next column.
    line2b = next_line(line, 10, 9999999)
    a2b, line3b = next_action(actions, a + 1, line2b, next_line, *args)
    linesb = unroll(line2b, line3b)
    if linesb[0].column is linesb[1].column:
        return a2b, line3b

    # We were still separated from our content?  Give up and keep
    # ourselves on our original page.
    return a2, line3
#next_line(line, 10, 2)

def run(actions, line, next_line):
    a = 0
    while a < len(actions):
        action, *args = actions[a]
        a, line = action(actions, a, line, next_line, *args)
    return line

def test_title_without_anything_after_it():
    actions = [
        (section_title, 'Title'),
    ]
    line = run(actions, None, next_line)
    assert line.previous is None

def test_title_with_stuff_after_it():
    # A title followed by a happy paragraph should stay in place.
    actions = [
        (section_title, 'Title'),
        (make_paragraph2, 10, 2, 1),
    ]
    line = run(actions, None, next_line)
    assert line.previous.previous is None
    return

def test_title_without_enough_room():
    actions = [
        (make_paragraph2, 10, 2, 2),
        (section_title, 'Title'),
        (make_paragraph2, 10, 2, 1),
    ]
    l4 = run(actions, None, next_line)
    l3 = l4.previous
    l2 = l3.previous
    l1 = l2.previous

    p = Page(10, 34)
    c1 = Column(p, 1, 10, 34)
    c2 = Column(p, 2, 10, 34)
    assert l1 == Line(None, c1, 10, [])
    assert l2 == Line(l1, c1, 22, [])
    assert l3 == Line(l2, c2, 10, [])
    assert l4 == Line(l3, c2, 22, [])
