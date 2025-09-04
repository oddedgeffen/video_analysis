import { createTheme, responsiveFontSizes } from '@mui/material/styles';

// Define the custom color palette
const palette = {
  primary: {
    main: '#2563eb', // Bold blue
    light: '#60a5fa',
    dark: '#1e40af',
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#9333ea', // Purple
    light: '#a855f7',
    dark: '#7e22ce',
    contrastText: '#ffffff',
  },
  success: {
    main: '#059669', // Green
    light: '#10b981',
    dark: '#047857',
  },
  error: {
    main: '#dc2626', // Red
    light: '#ef4444',
    dark: '#b91c1c',
  },
  warning: {
    main: '#d97706', // Amber
    light: '#f59e0b',
    dark: '#b45309',
  },
  info: {
    main: '#0284c7', // Sky blue
    light: '#0ea5e9',
    dark: '#0369a1',
  },
  grey: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
  },
  background: {
    default: '#f9fafb',
    paper: '#ffffff',
    dark: '#111827',
  },
  text: {
    primary: '#111827',
    secondary: '#4b5563',
    disabled: '#9ca3af',
  },
};

// Define custom typography
const typography = {
  fontFamily: [
    'Inter',
    '-apple-system',
    'BlinkMacSystemFont',
    '"Segoe UI"',
    'Roboto',
    '"Helvetica Neue"',
    'Arial',
    'sans-serif',
  ].join(','),
  h1: {
    fontWeight: 700,
    fontSize: '2.5rem',
    lineHeight: 1.2,
  },
  h2: {
    fontWeight: 700,
    fontSize: '2rem',
    lineHeight: 1.3,
  },
  h3: {
    fontWeight: 600,
    fontSize: '1.75rem',
    lineHeight: 1.4,
  },
  h4: {
    fontWeight: 600,
    fontSize: '1.5rem',
    lineHeight: 1.4,
  },
  h5: {
    fontWeight: 600,
    fontSize: '1.25rem',
    lineHeight: 1.4,
  },
  h6: {
    fontWeight: 600,
    fontSize: '1rem',
    lineHeight: 1.4,
  },
  subtitle1: {
    fontSize: '1.125rem',
    fontWeight: 500,
  },
  subtitle2: {
    fontSize: '0.875rem',
    fontWeight: 500,
  },
  body1: {
    fontSize: '1rem',
    lineHeight: 1.5,
  },
  body2: {
    fontSize: '0.875rem',
    lineHeight: 1.5,
  },
  button: {
    fontSize: '0.875rem',
    fontWeight: 600,
    textTransform: 'none',
  },
  caption: {
    fontSize: '0.75rem',
    lineHeight: 1.5,
  },
  overline: {
    fontSize: '0.75rem',
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  },
};

// Create the theme with custom components
const baseTheme = createTheme({
  palette,
  typography,
  shape: {
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          boxShadow: 'none',
          '&:hover': {
            boxShadow: '0 4px 8px rgba(0, 0, 0, 0.1)',
          },
          textTransform: 'none',
          padding: '8px 20px',
        },
        contained: {
          '&:hover': {
            boxShadow: '0 6px 12px rgba(0, 0, 0, 0.1)',
          },
        },
        containedPrimary: {
          background: `linear-gradient(135deg, ${palette.primary.main}, ${palette.primary.dark})`,
        },
        containedSecondary: {
          background: `linear-gradient(135deg, ${palette.secondary.main}, ${palette.secondary.dark})`,
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
        },
        elevation1: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)',
        },
        elevation2: {
          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.1)',
        },
        elevation3: {
          boxShadow: '0 3px 6px rgba(0, 0, 0, 0.05), 0 3px 6px rgba(0, 0, 0, 0.1)',
        },
        elevation4: {
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.05), 0 4px 8px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          overflow: 'hidden',
          transition: 'transform 0.3s ease, box-shadow 0.3s ease',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.08)',
          },
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '&:hover fieldset': {
              borderColor: palette.primary.main,
            },
          },
        },
      },
    },
    MuiCssBaseline: {
      styleOverrides: {
        html: {
          scrollBehavior: 'smooth',
        },
        body: {
          scrollbarWidth: 'thin',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            background: palette.grey[100],
          },
          '&::-webkit-scrollbar-thumb': {
            background: palette.grey[300],
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            background: palette.grey[400],
          },
        },
      },
    },
  },
});

// Make typography responsive
const theme = responsiveFontSizes(baseTheme);

export default theme; 