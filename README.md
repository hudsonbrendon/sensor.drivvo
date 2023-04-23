![hacs_badge](https://img.shields.io/badge/hacs-custom-orange.svg) [![BuyMeCoffee][buymecoffeebedge]][buymecoffee]

# Drivvo Sensor Component

![logo.jpg](logo.png)

Componente customizado para obter informações presentes no [drivvo.com](https://www.drivvo.com/pt) para o home assistant.

# Instalação

## HACS

- Tenha o [HACS](https://hacs.xyz/) instalado, isso permitirá que você atualize facilmente.
- Adicione https://github.com/hudsonbrendon/sensor.drivvo como um repositório personalizado do Tipo: Integração
- Clique em Instalar na integração "Drivvo".
- Reinicie Home-Assistant.

## Manual

- Copie o diretório custom_components/drivvo para o seu diretório <config dir>/custom_components.
- Configure.
- Reinicie o Home-Assistant.

## Configuração

Adicionar o Drivvo à sua instância do Home Assistant pode ser feito por meio da interface do usuário, usando este botão:

[![image](https://user-images.githubusercontent.com/31328123/189550000-6095719b-ca38-4860-b817-926b19de1b32.png)](https://my.home-assistant.io/redirect/config_flow_start?domain=drivvo)

### Configuração Manual
Se o botão Meu acima não funcionar, você também pode executar as seguintes etapas manualmente:

* Navegue até sua instância do Home Assistant.
* Na barra lateral, clique em Configurações.
* No menu de configuração, selecione: Dispositivos & serviços.
* No canto inferior direito, clique no botão Adicionar integração.
* Na lista, pesquise e selecione “Drivvo”.
* Siga as instruções na tela para concluir a configuração.

# Construindo um card

Para visualizar as informações dos drivvo, segue um exemplo de um card. Lembre-se de substituir as entidades presentes no card pelas suas entidades.


```yaml
type: custom:config-template-card
entities:
  - sensor.nissan_march_abastecimento
card:
  type: entities
  show_header_toggle: 'off'
  style: |
    .card-header {
      padding: 0px 0px 0px 0px !important;
    }
  entities:
    - type: custom:hui-vertical-stack-card
      cards:
        - type: horizontal-stack
          cards:
            - type: picture
              style: |
                ha-card { 
                    --paper-card-background-color: 'rgba(0, 0, 0, 0.0)';
                    --ha-card-background: "rgba(0, 0, 0, 0.0)";
                    --ha-card-box-shadow: 'none';
                }
              image: /local/images/nissan.png
            - type: custom:button-card
              layout: icon_name_state2nd
              show_icon: true
              show_state: true
              styles:
                grid:
                  - grid-template-columns: 50px auto
                icon:
                  - padding: 0px 0px
                  - height: 100px
                  - width: 30px
                card:
                  - '--ha-card-background': rgba(0, 0, 0, 0.0)
                  - '--ha-card-box-shadow': none
                state:
                  - padding: 0px 10px
                  - justify-self: start
                  - font-family: Roboto, sans-serif
                  - font-size: 15px
                name:
                  - padding: 0px 10px
                  - justify-self: start
                  - color: var(--secondary-text-color)
              entity: device_tracker.nissan_march
              name: Localização
              icon: mdi:car
        - type: custom:bar-card
          show_icon: true
          align: split
          columns: 1
          max: 41
          positions:
            icon: inside
            indicator: inside
            name: inside
            value: inside
          unit_of_measurement: Litros
          animation: 'on'
          severity:
            - color: '#fd0000'
              from: 1
              to: 19
            - color: '#ffaa00'
              from: 20
              to: 29
            - color: '#2CE026'
              from: 30
              to: 41
          style: |
            ha-card { 
                --paper-card-background-color: 'rgba(0, 0, 0, 0.0)';
                --ha-card-background: "rgba(0, 0, 0, 0.0)";
                --paper-item-icon-color: 'var(--text-primary-color';
                --ha-card-box-shadow: 'none';
            }
          entities:
            - entity: sensor.nissan_march_abastecimento
              attribute: volume_de_combustivel
          name: Volume de combustível
          entity_row: true
        - type: custom:apexcharts-card
          chart_type: line
          header:
            title: Nissan March
            show: true
            show_states: true
            colorize_states: true
          series:
            - entity: sensor.nissan_march_abastecimento
              attribute: odometro
              type: column
              name: Odômetro
              unit: km
            - entity: sensor.nissan_march_abastecimento
              attribute: preco_do_combustivel
              type: column
              name: Preço atual da gasolina
              unit: R$
              float_precision: 2
            - entity: sensor.nissan_march_abastecimento
              attribute: valor_total_pago
              type: column
              name: Valor total pago
              unit: R$
              float_precision: 2
            - entity: sensor.nissan_march_abastecimento
              attribute: soma_total_de_valores_pagos_em_todos_os_abastecimentos
              type: column
              name: Total pago em todos os abestecimentos até então
              unit: R$
              float_precision: 2
            - entity: sensor.nissan_march_abastecimento
              attribute: km_percorridos_desde_o_ultimo_abastecimento
              type: column
              name: Kms percorridos desde o último abastecimento
              unit: Km
            - entity: sensor.gasolina_media_natal
              type: column
              name: Preço médio da gasolina
              unit: R$
              float_precision: 2
            - entity: sensor.nissan_march_abastecimento
              type: column
              name: Abastecimentos
              unit: Abastecimentos
```

Após a configuração, o card acima ficará com essa aparência:

![image](https://user-images.githubusercontent.com/5201888/201997053-d025824d-11e2-4e53-8dcf-e011d1b267f2.png)

# Debugando

```yaml
logger:
  default: info
  logs:
    custom_components.drivvo: debug
```

[buymecoffee]: https://www.buymeacoffee.com/hudsonbrendon
[buymecoffeebedge]: https://camo.githubusercontent.com/cd005dca0ef55d7725912ec03a936d3a7c8de5b5/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6275792532306d6525323061253230636f666665652d646f6e6174652d79656c6c6f772e737667
