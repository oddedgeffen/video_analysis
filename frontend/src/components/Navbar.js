import React, { useState, useEffect } from 'react';
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  Container,
  Avatar,
  Button,
  Tooltip,
  MenuItem,
  useScrollTrigger,
  Slide,
  useTheme,
  useMediaQuery,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Home as HomeIcon,
  Article as ArticleIcon,
  WorkOutline as WorkIcon,
  Settings as SettingsIcon,
  HelpOutline as HelpIcon,
  Login as LoginIcon,
  AccountCircle,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

// Hide AppBar on scroll down
function HideOnScroll(props) {
  const { children } = props;
  const trigger = useScrollTrigger();

  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {children}
    </Slide>
  );
}

// Logo component with animation
const Logo = () => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.5 }}
    >
      <Typography
        variant="h6"
        noWrap
        component="div"
        sx={{
          mr: 2,
          display: { xs: 'none', md: 'flex' },
          fontWeight: 700,
          color: 'white',
          textDecoration: 'none',
        }}
      >
        LOGO SAAS
      </Typography>
    </motion.div>
  );
};

const MobileDrawer = ({ open, onClose, navItems }) => {
  return (
    <Drawer anchor="left" open={open} onClose={onClose}>
      <Box sx={{ width: 250, pt: 2 }}>
        <Typography variant="h6" sx={{ px: 2, py: 1, fontWeight: 'bold' }}>
          LOGO SAAS
        </Typography>
        <Divider />
        <List>
          {navItems.map((item) => (
            <ListItem button key={item.label} onClick={onClose}>
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItem>
          ))}
        </List>
      </Box>
    </Drawer>
  );
};

const Navbar = () => {
  const [anchorElUser, setAnchorElUser] = useState(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  // Settings menu handlers
  const handleOpenUserMenu = (event) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  // Mobile drawer handlers
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  // Navigation items
  const navItems = [
    { label: 'Home', icon: <HomeIcon />, path: '/' },
    { label: 'Documents', icon: <ArticleIcon />, path: '/documents' },
    { label: 'Projects', icon: <WorkIcon />, path: '/projects' },
  ];

  const settings = ['Profile', 'Account', 'Dashboard', 'Logout'];

  return (
    <HideOnScroll>
      <AppBar position="sticky" elevation={0}>
        <Container maxWidth="xl">
          <Toolbar disableGutters>
            {/* Mobile menu button */}
            {isMobile && (
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ mr: 2 }}
              >
                <MenuIcon />
              </IconButton>
            )}

            {/* Logo */}
            <Logo />

            {/* Mobile Logo */}
            <Typography
              variant="h6"
              noWrap
              component="div"
              sx={{
                flexGrow: 1,
                display: { xs: 'flex', md: 'none' },
                fontWeight: 700,
              }}
            >
              LOGO SAAS
            </Typography>

            {/* Desktop navigation */}
            <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
              {navItems.map((item) => (
                <motion.div
                  key={item.label}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Button
                    sx={{
                      my: 2,
                      mx: 1,
                      color: 'white',
                      display: 'flex',
                      alignItems: 'center',
                    }}
                  >
                    {item.icon && (
                      <Box component="span" sx={{ mr: 1 }}>
                        {item.icon}
                      </Box>
                    )}
                    {item.label}
                  </Button>
                </motion.div>
              ))}
            </Box>

            {/* User menu */}
            <Box sx={{ flexGrow: 0 }}>
              <motion.div whileHover={{ scale: 1.1 }} whileTap={{ scale: 0.9 }}>
                <Tooltip title="Open settings">
                  <IconButton onClick={handleOpenUserMenu} sx={{ p: 0 }}>
                    <Avatar sx={{ bgcolor: theme.palette.secondary.main }}>
                      <AccountCircle />
                    </Avatar>
                  </IconButton>
                </Tooltip>
              </motion.div>
              <Menu
                sx={{ mt: '45px' }}
                id="menu-appbar"
                anchorEl={anchorElUser}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorElUser)}
                onClose={handleCloseUserMenu}
              >
                {settings.map((setting) => (
                  <MenuItem key={setting} onClick={handleCloseUserMenu}>
                    <Typography textAlign="center">{setting}</Typography>
                  </MenuItem>
                ))}
              </Menu>
            </Box>
          </Toolbar>
        </Container>

        {/* Mobile drawer */}
        <MobileDrawer
          open={mobileOpen}
          onClose={handleDrawerToggle}
          navItems={navItems}
        />
      </AppBar>
    </HideOnScroll>
  );
};

export default Navbar; 