package main

import (
	"encoding/csv"
	"encoding/json"
	"flag"
	"log"
	"net/http"
	"os"
	"strconv"
)

func readCSV(CSVURL string) ([][]string, error) {
	resp, err := http.Get(CSVURL)
	if err != nil {
		return nil, err
	}

	defer func() {
		_ = resp.Body.Close()
	}()
	reader := csv.NewReader(resp.Body)
	reader.Comma = ','
	data, err := reader.ReadAll()
	if err != nil {
		return nil, err
	}

	return data, nil
}

type JSONData struct {
	Model  string         `json:"model"`
	Pk     int            `json:"pk"`
	Fields JSONDataFields `json:"fields"`
}

type JSONDataFields struct {
	Title            string `json:"title"`
	InitialPrompt    string `json:"initial_prompt"`
	AiName           string `json:"ai_name"`
	HumanName        string `json:"human_name"`
	SummarizeToken   int    `json:"summarize_token"`
	Info             string `json:"info"`
	Description      string `json:"description"`
	ResponseLength   int    `json:"response_length"`
	Temperature      string `json:"temperature"`
	TopP             string `json:"top_p"`
	FrequencyPenalty string `json:"frequency_penalty"`
	PresencePenalty  string `json:"presence_penalty"`
	Duration         int    `json:"duration"`
	Level            int    `json:"level"`
}

func mustInt(s string, row, col int) int {
	i, err := strconv.ParseInt(s, 10, 64)
	if err != nil {
		log.Fatalf("while parsing int (row: %v, col: %v): %s", row, col, err)
	}
	return int(i)
}

func main() {
	CSVURL := flag.String("csv-url", "https://docs.google.com/spreadsheets/d/e/2PACX-1vR9-l5WWtnAmGE9sKnr0hfn5RX-y1iaFdDxwJNRPrLSWc8pq0362vyFxic1uyhIOdwVyqiK-zBSpQf7/pub?gid=0&single=true&output=csv", "URI of CSV file to read data from.")
	outPath := flag.String("o", "./output.json", "Output JSON path.")
	flag.Parse()
	data, err := readCSV(*CSVURL)
	if err != nil {
		log.Fatalf("while fetching and reading CSV (maybe not published?): %s", err)
	}
	if len(data) == 0 {
		log.Fatal("while validating CSV: length of CSV rows is 0")
	}
	jsonData := make([]JSONData, len(data)-1)
	for i, row := range data {
		if i == 0 {
			continue
		}
		jsonData[i-1] = JSONData{
			Model: "demo.scenario",
			Pk:    i, // start from 1
			Fields: JSONDataFields{
				Title:            row[0],
				InitialPrompt:    row[1],
				AiName:           row[2],
				HumanName:        row[3],
				SummarizeToken:   mustInt(row[4], i, 4),
				Info:             row[5],
				Description:      row[6],
				ResponseLength:   mustInt(row[7], i, 7),
				Temperature:      row[8],
				TopP:             row[9],
				FrequencyPenalty: row[10],
				PresencePenalty:  row[11],
				Duration:         mustInt(row[12], i, 12),
				Level:            mustInt(row[13], i, 13),
			},
		}
		log.Printf("done row %v/%v.", i, len(data)-1)
	}
	f, err := os.Create(*outPath)
	if err != nil {
		log.Fatalf("while opening output file: %s", err)
	}
	b, err := json.Marshal(jsonData)
	if err != nil {
		log.Fatalf("while marshalling data: %s", err)
	}
	_, err = f.Write(b)
	if err != nil {
		log.Fatalf("while writing data to file: %s", err)
	}
	_ = f.Close()
	log.Printf("wrote to %s.", *outPath)
}
