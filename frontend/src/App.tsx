import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { theme } from './theme';
import { BlueprintStatusView } from './views/BlueprintStatusView';

export function App() {
    return (
        <ThemeProvider theme={theme}>
            <CssBaseline />
            <Router>
                <Routes>
                    {/* Add your existing routes here */}
                    <Route 
                        path="/topics/:topicId/blueprints/:blueprintId/status" 
                        element={<BlueprintStatusView />} 
                    />
                </Routes>
            </Router>
        </ThemeProvider>
    );
}
