import os
import sqlite3

class NgramDB():
    def __init__(self, filename):
        assert os.path.isfile(filename)

        self.db = sqlite3.connect(filename)
        self._cursor = self.db.cursor()

    def __exit__(self, type, value, traceback):
        self.db.close()

    def _get_count(self, form):
        self._cursor.execute("SELECT count FROM ngram WHERE phrase = ?", (form,))
        return next(self._cursor, [0])[0]

    def get_count(self, form):
        # Returns the number of times "form" appears in the corpus

        # If len(form)>5, it is impossible to know with certainty, ex
        # "a b c d e f" will appear to exist in "a b c d e | b c d e f"
        # In this case, it will return the 5-word subitem with the lowest
        # matching count, which is the maximum number of times form could
        # appear, but the reality could be lower

        form_words = form.split()

        size = len(form_words)
        count = 0
        if size <= 5:
            return self._get_count(form)

        for offset in range(size-5+1):
            section = " ".join(form_words[offset:offset+5])

            section_count = self._get_count(section)

            if offset == 0 or section_count < count:
                count = section_count
                if not count:
                    return count

        return count

