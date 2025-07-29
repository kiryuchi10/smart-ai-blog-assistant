import { render, screen } from '@testing-library/react';
import App from './App';

test('renders AI Blog Assistant heading', () => {
  render(<App />);
  const headingElement = screen.getByText(/AI Blog Assistant/i);
  expect(headingElement).toBeInTheDocument();
});

test('renders get started button', () => {
  render(<App />);
  const buttonElement = screen.getByText(/Get Started/i);
  expect(buttonElement).toBeInTheDocument();
});