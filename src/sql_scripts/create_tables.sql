CREATE TABLE Chapter (
    id INTEGER PRIMARY KEY,
    ChapterName TEXT,
    Description TEXT
);

CREATE TABLE Section (
    id INTEGER PRIMARY KEY,
    ChapterId INTEGER,
    SectionName TEXT,
    Description TEXT,
    FOREIGN KEY(ChapterId) REFERENCES Chapter(id)
);

CREATE TABLE Expense (
    id INTEGER PRIMARY KEY,
    ChapterId INTEGER, -- dzial - 3 digits value 
    --SectionId INTEGER, -- rozdzial - 4 digits value
    TaskName TEXT,
    FinancialNeed INTEGER,
    FOREIGN KEY(ChapterId) REFERENCES Chapter(id)--,
    --FOREIGN KEY(SectionId) REFERENCES Section(id)
);
