import 'package:flutter/material.dart';

import 'di/app_dependencies.dart';
import 'presentation/pages/home_page.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(AuthenticatorApp(dependencies: AppDependencies.create()));
}

class AuthenticatorApp extends StatelessWidget {
  const AuthenticatorApp({super.key, required this.dependencies});

  final AppDependencies dependencies;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Mi Authenticator',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: Colors.indigo, useMaterial3: true),
      darkTheme: ThemeData(colorSchemeSeed: Colors.indigo, brightness: Brightness.dark, useMaterial3: true),
      home: HomePage(
        controller: dependencies.accountsController,
        generateCode: dependencies.generateCode,
      ),
    );
  }
}
