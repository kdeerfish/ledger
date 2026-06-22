package internal

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

// DefaultBaseURL is the default Ledger API address.
const DefaultBaseURL = "http://127.0.0.1:5800"

// Client talks to the Ledger HTTP API.
type Client struct {
	BaseURL    string
	HTTPClient *http.Client
}

// NewClient creates a Client. It reads LEDGER_API_URL from the environment
// when set; otherwise it falls back to DefaultBaseURL.
func NewClient() *Client {
	base := strings.TrimRight(os.Getenv("LEDGER_API_URL"), "/")
	if base == "" {
		base = DefaultBaseURL
	}
	return &Client{
		BaseURL: base,
		HTTPClient: &http.Client{
			Timeout: 15 * time.Second,
		},
	}
}

// ──────────────────── low-level helpers ────────────────────

// Get performs GET and returns the raw body bytes.
func (c *Client) Get(path string, params map[string]string) ([]byte, error) {
	u := c.BaseURL + path
	if len(params) > 0 {
		q := url.Values{}
		for k, v := range params {
			if v != "" {
				q.Set(k, v)
			}
		}
		u += "?" + q.Encode()
	}
	resp, err := c.HTTPClient.Get(u)
	if err != nil {
		return nil, fmt.Errorf("GET %s: %w", path, err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return body, fmt.Errorf("HTTP %d: %s", resp.StatusCode, body)
	}
	return body, nil
}

// PostJSON performs POST with a JSON body.
func (c *Client) PostJSON(path string, data any) ([]byte, error) {
	return c.doJSON(http.MethodPost, path, data)
}

// PutJSON performs PUT with a JSON body.
func (c *Client) PutJSON(path string, data any) ([]byte, error) {
	return c.doJSON(http.MethodPut, path, data)
}

// Delete performs DELETE.
func (c *Client) Delete(path string) ([]byte, error) {
	req, _ := http.NewRequest(http.MethodDelete, c.BaseURL+path, nil)
	return c.do(req)
}

func (c *Client) doJSON(method, path string, data any) ([]byte, error) {
	var body io.Reader
	if data != nil {
		b, err := json.Marshal(data)
		if err != nil {
			return nil, fmt.Errorf("marshal: %w", err)
		}
		body = bytes.NewReader(b)
	}
	req, err := http.NewRequest(method, c.BaseURL+path, body)
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	return c.do(req)
}

func (c *Client) do(req *http.Request) ([]byte, error) {
	resp, err := c.HTTPClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("%s %s: %w", req.Method, req.URL.Path, err)
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return b, fmt.Errorf("HTTP %d: %s", resp.StatusCode, b)
	}
	return b, nil
}

// ──────────────────── response helpers ────────────────────

// APIResponse is the standard Ledger API envelope.
type APIResponse struct {
	Success bool            `json:"success"`
	Data    json.RawMessage `json:"data,omitempty"`
	Error   string          `json:"error,omitempty"`
	Message string          `json:"message,omitempty"`
}

// Parse unmarshals the standard response envelope.
func Parse(body []byte) (*APIResponse, error) {
	var r APIResponse
	if err := json.Unmarshal(body, &r); err != nil {
		return nil, fmt.Errorf("decode response: %w", err)
	}
	if !r.Success {
		return &r, fmt.Errorf("API error: %s", r.Error)
	}
	return &r, nil
}

// PrintJSON pretty-prints any value as JSON to stdout.
func PrintJSON(v any) {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	enc.Encode(v)
}

// PrintResponse parses and pretty-prints an API response.
func PrintResponse(body []byte) {
	var raw any
	if err := json.Unmarshal(body, &raw); err != nil {
		fmt.Println(string(body))
		return
	}
	PrintJSON(raw)
}
